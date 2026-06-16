import logging
import sys
from datetime import timedelta
from uuid import uuid4
import os
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure backend/ is on sys.path so "config", "core" etc. resolve
# regardless of whether you run from project root or backend/
_backend_dir = str(Path(__file__).parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import Response
from pydantic import BaseModel, field_validator
from livekit import api
from sqlmodel import Session, text
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config.logging import configure_logging
from config.settings import load_settings
from core.database import init_db, sync_local_to_cloud, engine_local, Clinic
from core.auth import verify_password, get_password_hash, create_access_token, get_current_clinic_id, ACCESS_TOKEN_EXPIRE_MINUTES

configure_logging()
logger = logging.getLogger(__name__)

settings = load_settings()

limiter = Limiter(key_func=get_remote_address)

async def background_sync_task():
    """Runs the database sync job every 60 seconds while the server is alive."""
    while True:
        try:
            await asyncio.to_thread(sync_local_to_cloud)
        except Exception as e:
            logger.error("Background sync error: %s", e)
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(background_sync_task())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

MAX_BODY_SIZE = 1_048_576  # 1 MB


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_SIZE:
        return Response(status_code=413, content="Request body too large")
    return await call_next(request)

allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TokenRequest(BaseModel):
    room: str | None = None
    identity: str | None = None
    clinic_id: str | None = None

class RegisterRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_min_length(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 3:
            raise ValueError("Username must be at least 3 characters")
        return stripped

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

@app.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest):
    """Create a new clinic account."""
    with Session(engine_local) as session:
        existing = session.get(Clinic, body.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A clinic with this ID already exists",
            )

        hashed = get_password_hash(body.password)
        clinic = Clinic(id=body.username, hashed_password=hashed)
        session.add(clinic)
        session.commit()

    return {"message": f"Clinic '{body.username}' registered successfully"}

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate clinic and return a JWT."""
    with Session(engine_local) as session:
        clinic = session.get(Clinic, form_data.username)
        if not clinic or not verify_password(form_data.password, clinic.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": clinic.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def create_room_and_dispatch(room_name: str) -> None:
    lkapi = api.LiveKitAPI(
        settings.livekit.url,
        settings.livekit.api_key,
        settings.livekit.api_secret,
    )
    try:
        await lkapi.room.create_room(api.CreateRoomRequest(name=room_name))
        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(room=room_name, agent_name=settings.agent.name)
        )
    except Exception as e:
        logger.warning("Room creation or dispatch failed for room '%s': %s", room_name, e)
        raise
    finally:
        await lkapi.aclose()


@app.post("/token")
@limiter.limit("20/minute")
async def token(
    request: Request,
    body: TokenRequest,
    clinic_id: str = Depends(get_current_clinic_id) # Protect this endpoint
):
    room_name = body.room or settings.agent.default_room

    if len(room_name) > 64 or not room_name.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(status_code=422, detail="Invalid room name: must be <= 64 characters, alphanumeric with - and _")

    identity = (
        body.identity.strip()
        if body.identity and body.identity.strip()
        else f"browser-{uuid4().hex[:8]}"
    )

    # Store clinic_id in room metadata so the agent knows which clinic to save data for
    room_name = f"{clinic_id}_{room_name}"

    # Create room and dispatch agent before returning the token
    # This ensures the user never connects to an empty room
    await create_room_and_dispatch(room_name)

    jwt = (
        api.AccessToken(settings.livekit.api_key, settings.livekit.api_secret)
        .with_identity(identity)
        .with_name(identity)
        .with_ttl(timedelta(hours=1))
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .to_jwt()
    )

    return {
        "token": jwt,
        "url": settings.livekit.url,
        "room": room_name,
        "identity": identity,
        "clinic_id": clinic_id,
    }

@app.get("/health")
async def health():
    """Health check endpoint for Docker / load balancer probes."""
    db_ok = True
    try:
        with Session(engine_local) as session:
            session.exec(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": "connected" if db_ok else "unreachable"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "token_server:app",
        host="0.0.0.0",
        port=8080,
        limit_max_request_body=MAX_BODY_SIZE,
    )

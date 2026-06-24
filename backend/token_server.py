import logging
import sys
import time
from datetime import timedelta
from uuid import uuid4
import os
import asyncio
from collections import defaultdict
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
    if content_length:
        try:
            if int(content_length) > MAX_BODY_SIZE:
                return Response(status_code=413, content="Request body too large")
        except ValueError:
            return Response(status_code=400, content="Invalid Content-Length header")
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
        if len(v) > 128:
            raise ValueError("Password must be at most 128 characters")
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
                detail={
                    "error_code": "AUTH_DUPLICATE_USERNAME",
                    "message": "A clinic with this ID already exists",
                },
            )

        hashed = get_password_hash(body.password)
        clinic = Clinic(id=body.username, hashed_password=hashed)
        session.add(clinic)
        session.commit()

    return {"message": f"Clinic '{body.username}' registered successfully"}

# In-memory failed login attempt tracker
# {username: (attempt_count, locked_until_timestamp)}
_failed_logins: dict[str, tuple[int, float]] = defaultdict(lambda: (0, 0.0))
_MAX_LOGIN_ATTEMPTS = 5
_LOCKOUT_SECONDS = 900  # 15 minutes

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate clinic and return a JWT."""
    username = form_data.username
    attempts, locked_until = _failed_logins[username]
    now = time.monotonic()

    if locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error_code": "AUTH_LOCKED",
                "message": f"Account locked. Try again in {int(locked_until - now)} seconds.",
            },
        )

    with Session(engine_local) as session:
        clinic = session.get(Clinic, username)
        if not clinic or not verify_password(form_data.password, clinic.hashed_password):
            attempts += 1
            if attempts >= _MAX_LOGIN_ATTEMPTS:
                _failed_logins[username] = (0, now + _LOCKOUT_SECONDS)
                logger.warning("Account '%s' locked for %ds after %d failed attempts", username, _LOCKOUT_SECONDS, attempts)
            else:
                _failed_logins[username] = (attempts, 0.0)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_code": "AUTH_INVALID_CREDENTIALS",
                    "message": "Incorrect username or password",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Successful login — reset counter
    _failed_logins[username] = (0, 0.0)

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
        raise HTTPException(status_code=422, detail={
            "error_code": "TOKEN_INVALID_ROOM",
            "message": "Invalid room name: must be <= 64 characters, alphanumeric with - and _",
        })

    identity = (
        body.identity.strip()
        if body.identity and body.identity.strip()
        else f"browser-{uuid4().hex[:8]}"
    )

    if len(identity) > 64 or not identity.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(status_code=422, detail={
            "error_code": "TOKEN_INVALID_IDENTITY",
            "message": "Invalid identity: must be <= 64 characters, alphanumeric with - and _",
        })

    # Store clinic_id in room metadata so the agent knows which clinic to save data for
    room_name = f"{clinic_id}_{room_name}"

    # Create room and dispatch agent before returning the token
    # This ensures the user never connects to an empty room
    try:
        await create_room_and_dispatch(room_name)
    except Exception as exc:
        logger.error("Failed to create room or dispatch agent for '%s': %s", room_name, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "TOKEN_ROOM_FAILED",
                "message": "Unable to prepare your consultation room. Please try again.",
            },
            headers={"Retry-After": "5"},
        ) from exc

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

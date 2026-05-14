from datetime import timedelta
from uuid import uuid4
import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from livekit import api
from sqlmodel import Session

from config.settings import load_settings
from core.database import sync_local_to_cloud, engine_local, Clinic
from core.auth import verify_password, create_access_token, get_current_clinic_id, ACCESS_TOKEN_EXPIRE_MINUTES

settings = load_settings()

async def background_sync_task():
    """Runs the database sync job every 60 seconds while the server is alive."""
    while True:
        try:
            await asyncio.to_thread(sync_local_to_cloud)
        except Exception as e:
            print(f"Background sync error: {e}")
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(background_sync_task())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

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

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
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
        try:
            await lkapi.room.create_room(api.CreateRoomRequest(name=room_name))
        except Exception:
            pass

        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(room=room_name, agent_name=settings.agent.name)
        )
    finally:
        await lkapi.aclose()


@app.post("/token")
async def token(
    request: TokenRequest,
    background_tasks: BackgroundTasks,
    clinic_id: str = Depends(get_current_clinic_id) # Protect this endpoint
):
    room_name = request.room or settings.agent.default_room

    identity = (
        request.identity.strip()
        if request.identity and request.identity.strip()
        else f"browser-{uuid4().hex[:8]}"
    )

    # Store clinic_id in room metadata so the agent knows which clinic to save data for
    room_name = f"{clinic_id}_{room_name}"

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

    background_tasks.add_task(create_room_and_dispatch, room_name)

    return {
        "token": jwt,
        "url": settings.livekit.url,
        "room": room_name,
        "identity": identity,
        "clinic_id": clinic_id,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("token_server:app", host="0.0.0.0", port=8080, reload=True)

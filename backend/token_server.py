from datetime import timedelta
from uuid import uuid4
import os

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from livekit import api

from config.settings import load_settings

app = FastAPI()

settings = load_settings()

# Secure CORS: Default to localhost in dev, but allow configuration via ENV
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
            # Room may already exist.
            pass

        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(room=room_name, agent_name=settings.agent.name)
        )
    finally:
        await lkapi.aclose()


class TokenRequest(BaseModel):
    room: str | None = None
    identity: str | None = None


@app.post("/token")
async def token(request: TokenRequest, background_tasks: BackgroundTasks):
    room_name = request.room or settings.agent.default_room

    identity = (
        request.identity.strip()
        if request.identity and request.identity.strip()
        else f"browser-{uuid4().hex[:8]}"
    )

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
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("token_server:app", host="0.0.0.0", port=8080, reload=True)

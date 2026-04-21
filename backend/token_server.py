import asyncio
from datetime import timedelta
from uuid import uuid4

from flask import Flask, jsonify, request
from flask_cors import CORS
from livekit import api

from config.settings import load_settings

app = Flask(__name__)
CORS(app)

settings = load_settings()


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


@app.route("/token", methods=["POST"])
def token():
    body = request.get_json() or {}
    room_name = body.get("room", settings.agent.default_room)
    requested_identity = body.get("identity")
    identity = (
        requested_identity.strip()
        if isinstance(requested_identity, str) and requested_identity.strip()
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

    try:
        asyncio.run(create_room_and_dispatch(room_name))
    except Exception as exc:
        # Keep returning token so frontend can still connect for debugging.
        print(f"Warning: Failed to dispatch agent: {exc}")

    return jsonify(
        {
            "token": jwt,
            "url": settings.livekit.url,
            "room": room_name,
            "identity": identity,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

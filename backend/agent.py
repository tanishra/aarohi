import asyncio
import logging
import threading

from livekit import api
from livekit import agents

from config.settings import load_settings
from main import server

logger = logging.getLogger(__name__)


async def _auto_dispatch_playground_rooms() -> None:
    settings = load_settings()
    lkapi = api.LiveKitAPI(
        settings.livekit.url,
        settings.livekit.api_key,
        settings.livekit.api_secret,
    )
    dispatched_rooms: set[str] = set()

    try:
        while True:
            try:
                response = await lkapi.room.list_rooms(api.ListRoomsRequest())
                for room in response.rooms:
                    if room.name in dispatched_rooms or room.num_participants <= 0:
                        continue

                    existing_dispatches = await lkapi.agent_dispatch.list_dispatch(room.name)
                    if existing_dispatches:
                        dispatched_rooms.add(room.name)
                        continue

                    await lkapi.agent_dispatch.create_dispatch(
                        api.CreateAgentDispatchRequest(
                            room=room.name,
                            agent_name=settings.agent.name,
                        )
                    )
                    dispatched_rooms.add(room.name)
                    logger.info(
                        "Auto-dispatched agent %s into room %s",
                        settings.agent.name,
                        room.name,
                    )
            except Exception as exc:
                logger.debug("Playground auto-dispatch check failed: %s", exc)

            await asyncio.sleep(2)
    finally:
        await lkapi.aclose()


def _start_playground_auto_dispatcher() -> None:
    thread = threading.Thread(
        target=lambda: asyncio.run(_auto_dispatch_playground_rooms()),
        name="playground-auto-dispatcher",
        daemon=True,
    )
    thread.start()


if __name__ == "__main__":
    _start_playground_auto_dispatcher()
    agents.cli.run_app(server)

from livekit.agents import cli

from main import build_worker_options


if __name__ == "__main__":
    cli.run_app(build_worker_options())

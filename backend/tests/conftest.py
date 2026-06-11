import os

# Must be set before any module imports that trigger load_settings()
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["LIVEKIT_URL"] = "wss://test.livekit.cloud"
os.environ["LIVEKIT_API_KEY"] = "test-api-key"
os.environ["LIVEKIT_API_SECRET"] = "test-api-secret"
os.environ["OPENAI_API_KEY"] = "sk-test-openai"
os.environ["DEEPGRAM_API_KEY"] = "test-deepgram"
os.environ["SARVAM_API_KEY"] = "sk-test-sarvam"
os.environ["LOCAL_DB_PATH"] = ":memory:"
os.environ.pop("CLOUD_DB_URL", None)

import pytest

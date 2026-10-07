import os

def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

STATE_API_BASE_URL = os.getenv(
    "STATE_API_BASE_URL", "http://127.0.0.1:8000"
).rstrip("/")
DEMO_MODE = env_bool("DEMO_MODE", True)
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/person3_progress.db")

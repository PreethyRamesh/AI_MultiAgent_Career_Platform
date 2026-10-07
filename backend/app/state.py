import json
import threading
from datetime import date, datetime, timedelta
from typing import Any

from . import config

_lock = threading.Lock()

_DEFAULT: dict[str, Any] = {
    "roadmap": None,
    "completed": [],
    "xp": 0,
    "streak": 0,
    "last_active": None,
    "mission_day": None,
    "mentor_history": [],
}


def _load() -> dict[str, Any]:
    if not config.STATE_FILE.exists():
        return dict(_DEFAULT)
    try:
        data = json.loads(config.STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT)
    state = dict(_DEFAULT)
    state.update(data)
    return state


def get_state() -> dict[str, Any]:
    with _lock:
        return _load()


def save_state(state: dict[str, Any]) -> None:
    with _lock:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        config.STATE_FILE.write_text(
            json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
        )


def update_state(**kwargs: Any) -> dict[str, Any]:
    with _lock:
        state = _load()
        state.update(kwargs)
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        config.STATE_FILE.write_text(
            json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return state


def reset_state() -> dict[str, Any]:
    with _lock:
        state = dict(_DEFAULT)
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        config.STATE_FILE.write_text(
            json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return state


def touch_streak(state: dict[str, Any]) -> dict[str, Any]:
    today = date.today().isoformat()
    last = state.get("last_active")
    if last == today:
        return state
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    state["streak"] = int(state.get("streak", 0)) + 1 if last == yesterday else 1
    state["last_active"] = today
    return state


def level_for_xp(xp: int) -> int:
    return max(1, xp // 250 + 1)

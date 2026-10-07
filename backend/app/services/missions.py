from datetime import date
from typing import Any

from ..models import MissionDay, MissionItem, Roadmap


def _flatten(roadmap: Roadmap) -> list[MissionItem]:
    items: list[MissionItem] = []
    for phase in roadmap.phases:
        for ms in phase.milestones:
            items.append(
                MissionItem(
                    id=ms.id,
                    milestone_id=ms.id,
                    phase_id=phase.id,
                    title=ms.title,
                    type=ms.type,
                    xp=ms.xp,
                )
            )
    return items


def build_day(roadmap: Roadmap, completed: list[str]) -> MissionDay:
    today = date.today().isoformat()
    pending = [i for i in _flatten(roadmap) if i.milestone_id not in completed]
    per_day = max(1, min(5, round(roadmap.hours_per_week / 2.5)))
    items = pending[:per_day]
    if not items and completed:
        items = [
            MissionItem(
                id="review-today",
                milestone_id="",
                phase_id="",
                title="Victory lap: review your notes and mentor one peer",
                type="review",
                xp=30,
            )
        ]
    for item in items:
        item.done = False
    return MissionDay(date=today, items=items)


def ensure_today(state: dict[str, Any]) -> MissionDay:
    roadmap_data = state.get("roadmap")
    today = date.today().isoformat()
    saved = state.get("mission_day")
    if saved and saved.get("date") == today:
        return MissionDay(**saved)
    if not roadmap_data:
        return MissionDay(date=today, items=[])
    roadmap = Roadmap(**roadmap_data)
    day = build_day(roadmap, state.get("completed", []))
    state["mission_day"] = day.model_dump()
    return day

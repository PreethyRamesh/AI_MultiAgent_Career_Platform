from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from . import state as store
from .models import (
    ChatIn,
    CompleteIn,
    MentorReply,
    MissionDay,
    ProfileIn,
    ProgressOut,
    Roadmap,
    SkillTreeOut,
)
from .services import mentor, missions, roadmap, skill_tree

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="AI Learning & Guidance Module", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/api/roadmap")
async def create_roadmap(profile: ProfileIn) -> dict:
    if not profile.target_role.strip():
        raise HTTPException(status_code=422, detail="target_role is required")
    generated, source = await roadmap.build(profile)
    state = store.update_state(roadmap=generated.model_dump(), completed=[], xp=0, mission_day=None)
    missions.ensure_today(state)
    store.save_state(state)
    return {"roadmap": generated, "source": source, "progress": _progress(state)}


@app.get("/api/state")
def full_state() -> dict:
    state = store.get_state()
    day = missions.ensure_today(state)
    if state.get("mission_day") != day.model_dump():
        store.save_state(state)
    return {
        "roadmap": state.get("roadmap"),
        "missions": day,
        "progress": _progress(state),
        "mentor_history": state.get("mentor_history", []),
        "tree": skill_tree.build(state).model_dump(),
    }


@app.get("/api/missions/today")
def today_missions() -> MissionDay:
    state = store.get_state()
    day = missions.ensure_today(state)
    store.save_state(state)
    return day


@app.post("/api/missions/complete")
def complete_mission(payload: CompleteIn) -> dict:
    state = store.get_state()
    day = missions.ensure_today(state)
    item = next((i for i in day.items if i.id == payload.item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="mission item not found")
    if not item.done:
        item.done = True
        if item.milestone_id and item.milestone_id not in state["completed"]:
            state["completed"].append(item.milestone_id)
            state["xp"] = int(state.get("xp", 0)) + item.xp
            store.touch_streak(state)
    day_dict = day.model_dump()
    state["mission_day"] = day_dict
    store.save_state(state)
    return {
        "missions": MissionDay(**day_dict),
        "progress": _progress(state),
        "tree": skill_tree.build(state).model_dump(),
    }


@app.get("/api/skill-tree")
def get_skill_tree() -> SkillTreeOut:
    return skill_tree.build(store.get_state())


@app.post("/api/mentor")
async def mentor_chat(payload: ChatIn) -> MentorReply:
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="message is required")
    state = store.get_state()
    text, source = await mentor.reply(state, payload.message, payload.history)
    history = list(state.get("mentor_history", []))
    history.append({"role": "user", "content": payload.message})
    history.append({"role": "assistant", "content": text})
    store.update_state(mentor_history=history[-40:])
    return MentorReply(reply=text, source=source)


@app.post("/api/reset")
def reset() -> dict:
    return {"progress": _progress(store.reset_state())}


@app.get("/api/roadmap/current")
def current_roadmap() -> Roadmap:
    data = store.get_state().get("roadmap")
    if not data:
        raise HTTPException(status_code=404, detail="no roadmap yet")
    return Roadmap(**data)


def _progress(state: dict) -> ProgressOut:
    roadmap_data = state.get("roadmap")
    completed = list(state.get("completed", []))
    if not roadmap_data:
        return ProgressOut(xp=int(state.get("xp", 0)))
    total = sum(len(p.milestones) for p in Roadmap(**roadmap_data).phases)
    done = len([c for c in completed])
    return ProgressOut(
        xp=int(state.get("xp", 0)),
        level=store.level_for_xp(int(state.get("xp", 0))),
        streak=int(state.get("streak", 0)),
        completed_milestones=completed,
        total_milestones=total,
        completion_pct=round(100 * done / total, 1) if total else 0.0,
        roadmap_ready=True,
        target_role=roadmap_data.get("target_role", ""),
    )

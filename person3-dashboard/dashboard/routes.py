from datetime import date
from fastapi import APIRouter, HTTPException, Query
from .achievements import achievement_view, evaluate_and_award
from .database import get_history, init_db, upsert_snapshot
from .state_client import DEMO_STATE, get_state
from .config import DEMO_MODE

router = APIRouter()

def phase_progress(state):
    missions = state.get("missions") or []
    if not missions:
        return float(state.get("progress", {}).get("completion_pct", 0))
    done = sum(1 for m in missions if m.get("completed") is True)
    return round(done / len(missions) * 100, 2)

def hours_from_state(state):
    p = state.get("progress", {})
    for key in ("hours_invested", "hours", "study_hours"):
        if p.get(key) is not None:
            try:
                return float(p[key])
            except (TypeError, ValueError):
                pass
    return 0.0

@router.get("/dashboard", include_in_schema=False)
async def dashboard():
    from fastapi.responses import FileResponse
    return FileResponse("templates/dashboard.html")

@router.get("/analytics", include_in_schema=False)
async def analytics():
    from fastapi.responses import FileResponse
    return FileResponse("templates/analytics.html")

@router.get("/api/progress/summary")
async def summary():
    state = await get_state()
    return {
        "state": state,
        "next_mission": next((m for m in state["missions"] if not m.get("completed")), None),
        "phase_progress": phase_progress(state)
    }

@router.post("/api/progress/snapshot")
async def snapshot(user_id: str = Query("demo-user")):
    init_db()
    state = await get_state()
    p = state["progress"]
    upsert_snapshot(
        user_id, date.today().isoformat(), p["xp"], p["level"], p["streak"],
        p["completion_pct"], hours_from_state(state), phase_progress(state)
    )
    newly = evaluate_and_award(user_id, state)
    return {
        "success": True,
        "message": "Daily progress snapshot saved.",
        "snapshot_date": date.today().isoformat(),
        "snapshot": {**p, "phase_progress": phase_progress(state),
                     "hours_invested": hours_from_state(state)},
        "new_achievements": newly
    }

@router.get("/api/progress/history")
async def history(user_id: str = Query("demo-user"),
                  limit: int = Query(90, ge=1, le=365)):
    return {"history": get_history(user_id, limit)}

@router.get("/api/achievements")
async def achievements(user_id: str = Query("demo-user")):
    state = await get_state()
    newly = evaluate_and_award(user_id, state)
    return {"achievements": achievement_view(user_id), "newly_awarded": newly}

@router.post("/api/achievements/evaluate")
async def evaluate(user_id: str = Query("demo-user")):
    state = await get_state()
    newly = evaluate_and_award(user_id, state)
    return {"success": True, "newly_awarded": newly,
            "achievements": achievement_view(user_id)}

# Demo-only route. In production, Person 2 owns /api/state.
@router.get("/api/state", include_in_schema=False)
async def demo_state():
    if not DEMO_MODE:
        raise HTTPException(status_code=404,
                            detail="Person 3 does not own /api/state in production.")
    return DEMO_STATE

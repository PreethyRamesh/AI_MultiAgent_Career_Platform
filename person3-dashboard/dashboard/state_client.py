from typing import Any
import httpx
from .config import DEMO_MODE, STATE_API_BASE_URL

DEMO_STATE = {
    "role": "Data Scientist",
    "roadmap": [
        {"id":1,"title":"Python Foundations","completed":True},
        {"id":2,"title":"SQL & Databases","completed":True},
        {"id":3,"title":"Statistics","completed":True},
        {"id":4,"title":"Machine Learning","completed":False},
        {"id":5,"title":"Data Visualization","completed":False},
        {"id":6,"title":"Deployment","completed":False}
    ],
    "missions": [
        {"id":1,"title":"Complete Python Practice","completed":True,"phase":1},
        {"id":2,"title":"Build a SQL Analysis","completed":True,"phase":1},
        {"id":3,"title":"Train a Regression Model","completed":False,"phase":2},
        {"id":4,"title":"Create a Data Visualization","completed":False,"phase":2}
    ],
    "progress": {"xp":750,"level":4,"streak":7,"completion_pct":52},
    "skill_tree": [
        {"name":"Python","current":82,"target":90},
        {"name":"SQL","current":68,"target":80},
        {"name":"Machine Learning","current":52,"target":80},
        {"name":"Statistics","current":70,"target":85},
        {"name":"Visualization","current":61,"target":80}
    ]
}

def _number(value: Any, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def normalize_state(raw: dict) -> dict:
    p = raw.get("progress") or {}
    skills = raw.get("skill_tree") or raw.get("skills") or []
    normalized = []
    for s in skills:
        if isinstance(s, dict):
            normalized.append({
                "name": s.get("name") or s.get("skill") or "Skill",
                "current": _number(s.get("current", s.get("coverage", s.get("progress", 0)))),
                "target": _number(s.get("target", s.get("target_pct", 100)), 100)
            })
    return {
        "role": raw.get("role") or raw.get("target_role") or "Learner",
        "roadmap": raw.get("roadmap") or [],
        "missions": raw.get("missions") or [],
        "progress": {
            "xp": int(_number(p.get("xp", raw.get("xp", 0)))),
            "level": int(_number(p.get("level", raw.get("level", 1)), 1)),
            "streak": int(_number(p.get("streak", raw.get("streak", 0)))),
            "completion_pct": round(_number(
                p.get("completion_pct", p.get("completion", raw.get("completion_pct", 0)))
            ), 2)
        },
        "skill_tree": normalized
    }

async def get_state():
    if DEMO_MODE:
        return normalize_state(DEMO_STATE)
    url = f"{STATE_API_BASE_URL}/api/state"
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get(url)
        response.raise_for_status()
        return normalize_state(response.json())

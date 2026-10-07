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

def _roadmap_items(roadmap: Any, completed_ids: set) -> list:
    if isinstance(roadmap, list):
        return [x for x in roadmap if isinstance(x, dict)]
    if isinstance(roadmap, dict):
        items = []
        for phase in roadmap.get("phases") or []:
            if not isinstance(phase, dict):
                continue
            for ms in phase.get("milestones") or []:
                items.append({
                    "id": ms.get("id"),
                    "title": ms.get("title", ""),
                    "completed": ms.get("id") in completed_ids,
                    "phase": phase.get("id") or phase.get("title"),
                })
        return items
    return []

def _mission_items(missions: Any) -> list:
    if isinstance(missions, list):
        return [m for m in missions if isinstance(m, dict)]
    if isinstance(missions, dict):
        items = []
        for it in missions.get("items") or []:
            if not isinstance(it, dict):
                continue
            items.append({
                "id": it.get("id"),
                "title": it.get("title", ""),
                "completed": bool(it.get("done")),
                "phase": it.get("phase_id"),
                "type": it.get("type"),
                "xp": it.get("xp", 0),
            })
        return items
    return []

def _status_value(node: dict) -> float:
    if node.get("status") == "completed" or node.get("completed") is True:
        return 100.0
    if node.get("status") == "available":
        return 50.0
    return 0.0

def _skills_from_tree(raw: dict) -> list:
    tree = raw.get("tree") or raw.get("skill_tree") or raw.get("skills") or []
    nodes = tree.get("nodes") if isinstance(tree, dict) else tree
    nodes = [n for n in (nodes or []) if isinstance(n, dict)]
    if not nodes:
        return []
    if all("status" in n for n in nodes):
        agg: dict = {}
        for node in nodes:
            done = _status_value(node) >= 100
            names = node.get("skills") or [node.get("title") or "Skill"]
            for name in names:
                entry = agg.setdefault(name, {"done": 0, "total": 0})
                entry["total"] += 1
                entry["done"] += 1 if done else 0
        return [
            {"name": name,
             "current": round(100 * v["done"] / v["total"], 1),
             "target": 100}
            for name, v in agg.items()
        ]
    normalized = []
    for s in nodes:
        normalized.append({
            "name": s.get("name") or s.get("skill") or "Skill",
            "current": _number(s.get("current", s.get("coverage", s.get("progress", 0)))),
            "target": _number(s.get("target", s.get("target_pct", 100)), 100)
        })
    return normalized

def normalize_state(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raw = {}
    p = raw.get("progress") or {}
    roadmap = raw.get("roadmap") or []
    completed_ids = set(p.get("completed_milestones") or [])
    role = (
        raw.get("role")
        or p.get("target_role")
        or (roadmap.get("target_role") if isinstance(roadmap, dict) else None)
        or "Learner"
    )
    return {
        "role": role,
        "roadmap": _roadmap_items(roadmap, completed_ids),
        "missions": _mission_items(raw.get("missions") or []),
        "progress": {
            "xp": int(_number(p.get("xp", raw.get("xp", 0)))),
            "level": int(_number(p.get("level", raw.get("level", 1)), 1)),
            "streak": int(_number(p.get("streak", raw.get("streak", 0)))),
            "completion_pct": round(_number(
                p.get("completion_pct", p.get("completion", raw.get("completion_pct", 0)))
            ), 2)
        },
        "skill_tree": _skills_from_tree(raw)
    }

async def get_state():
    if DEMO_MODE:
        return normalize_state(DEMO_STATE)
    url = f"{STATE_API_BASE_URL}/api/state"
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url)
        response.raise_for_status()
        return normalize_state(response.json())

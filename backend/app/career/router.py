"""API router + state persistence for the AI Career Analysis module (Person 1).

Mount with one line:  app.include_router(career.router)

State is persisted to `app/data/career_state.json` — a separate file from
Person 2's `state.json`, so the two modules never clobber each other.
"""

import json
import threading
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException

from .. import config
from . import ai, analyzer, knowledge as kb
from .models import (
    CourseworkIn,
    FullAnalysisIn,
    JobIn,
    ProjectsIn,
    ResumeIn,
    SkillGapsOut,
    StudentProfile,
)

router = APIRouter(prefix="/api/career", tags=["career"])

CAREER_STATE_FILE = config.DATA_DIR / "career_state.json"

_lock = threading.Lock()

_DEFAULT: dict[str, Any] = {
    "profile": None,
    "resume": None,
    "projects": None,
    "coursework": None,
    "job": None,
    "analysis": None,
}


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------

def _load() -> dict[str, Any]:
    if not CAREER_STATE_FILE.exists():
        return dict(_DEFAULT)
    try:
        data = json.loads(CAREER_STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT)
    state = dict(_DEFAULT)
    state.update({k: v for k, v in data.items() if k in _DEFAULT})
    return state


def _save(state: dict[str, Any]) -> None:
    with _lock:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        CAREER_STATE_FILE.write_text(
            json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
        )


def _update(**kwargs: Any) -> dict[str, Any]:
    with _lock:
        state = _load()
        state.update(kwargs)
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        CAREER_STATE_FILE.write_text(
            json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return state


# ---------------------------------------------------------------------------
# Input endpoints
# ---------------------------------------------------------------------------

@router.get("/state")
def get_career_state() -> dict:
    return _load()


@router.post("/profile")
def save_profile(profile: StudentProfile) -> dict:
    _update(profile=profile.model_dump())
    return _load()


@router.post("/resume")
async def analyze_resume(payload: ResumeIn) -> dict:
    result = analyzer.analyze_resume(payload)
    if config.GEMINI_API_KEY:
        refined = await ai.refine_resume(payload.content)
        if refined and any(refined.values()):
            if not result["education"]:
                result["education"] = refined["education"]
            if not result["projects"]:
                result["projects"] = refined["projects"]
            if not result["experience"]:
                result["experience"] = refined["experience"]
            if not result["certifications"]:
                result["certifications"] = refined["certifications"]
            result["ai_source"] = "gemini"
    _update(resume={"content": payload.content, "result": result})
    return result


@router.post("/projects")
def analyze_projects(payload: ProjectsIn) -> dict:
    result = analyzer.analyze_projects(payload)
    _update(projects={"items": [p.model_dump() for p in payload.projects], "result": result})
    return result


@router.post("/coursework")
def analyze_coursework(payload: CourseworkIn) -> dict:
    result = analyzer.analyze_coursework(payload)
    _update(coursework={"items": [c.model_dump() for c in payload.courses], "result": result})
    return result


@router.post("/job")
async def analyze_job(payload: JobIn) -> dict:
    result = analyzer.analyze_job(payload)
    if config.GEMINI_API_KEY:
        refined = await ai.refine_job(payload.description)
        if refined and (refined["required_skills"] or refined["qualifications"]):
            req = []
            for name in refined["required_skills"]:
                canonical = kb.canonicalize(name) or name
                meta = kb.SKILLS.get(canonical)
                cat = meta["category"] if meta else "Other"
                if cat == "Soft Skills":
                    continue
                req.append({"name": canonical, "category": cat, "count": 1})
            if req:
                soft = []
                for name in refined["soft_skills"] or []:
                    canonical = kb.canonicalize(name) or name
                    meta = kb.SKILLS.get(canonical)
                    if meta and meta["category"] == "Soft Skills":
                        soft.append({"name": canonical, "category": "Soft Skills", "count": 1})
                result = {
                    **result,
                    "required_skills": req,
                    "soft_skills": soft,
                    "qualifications": refined["qualifications"] or result["qualifications"],
                    "technologies": [r["name"] for r in req],
                    "ai_source": "gemini",
                }
    _update(job={"title": payload.title, "description": payload.description, "result": result})
    return result


# ---------------------------------------------------------------------------
# Full analysis + helpers
# ---------------------------------------------------------------------------

def _saved_data(state: dict) -> dict:
    """Reusable payloads from saved state (with stored analysis results)."""
    profile = StudentProfile(**state["profile"]) if state.get("profile") else None
    resume_data = (state.get("resume") or {}).get("result")
    projects_data = (state.get("projects") or {}).get("result")
    coursework_data = (state.get("coursework") or {}).get("result")
    job_data = (state.get("job") or {}).get("result")
    return {
        "profile": profile,
        "resume_data": resume_data,
        "projects_data": projects_data,
        "coursework_data": coursework_data,
        "job_data": job_data,
    }


@router.post("/analyze")
async def run_full_analysis(payload: FullAnalysisIn) -> dict:
    state = _load()

    profile = payload.profile or (StudentProfile(**state["profile"]) if state.get("profile") else None)
    resume_data = (state.get("resume") or {}).get("result")
    projects_data = (state.get("projects") or {}).get("result")
    coursework_data = (state.get("coursework") or {}).get("result")
    job_data = (state.get("job") or {}).get("result")

    # Optional inline inputs override/replace saved ones.
    if payload.resume is not None:
        result = analyzer.analyze_resume(payload.resume)
        resume_data = result
        state["resume"] = {"content": payload.resume.content, "result": result}
    if payload.projects is not None:
        result = analyzer.analyze_projects(payload.projects)
        projects_data = result
        state["projects"] = {"items": [p.model_dump() for p in payload.projects.projects], "result": result}
    if payload.coursework is not None:
        result = analyzer.analyze_coursework(payload.coursework)
        coursework_data = result
        state["coursework"] = {"items": [c.model_dump() for c in payload.coursework.courses], "result": result}
    if payload.job is not None:
        result = analyzer.analyze_job(payload.job)
        job_data = result
        state["job"] = {"title": payload.job.title, "description": payload.job.description, "result": result}

    if profile is None and resume_data is None and projects_data is None and coursework_data is None:
        raise HTTPException(status_code=422, detail="Add a profile, resume, project or coursework first.")

    analysis = analyzer.full_analysis(
        profile or StudentProfile(),
        resume_data,
        projects_data,
        coursework_data,
        job_data,
    )

    state["profile"] = profile.model_dump() if profile else None
    state["analysis"] = analysis
    _save(state)
    return analysis


@router.post("/skill-gaps")
def career_skill_gaps() -> SkillGapsOut:
    """Integration contract for Person 2: publish gaps to POST /api/roadmap."""
    state = _load()
    analysis = state.get("analysis")
    if not analysis:
        saved = _saved_data(state)
        if not any([saved["profile"], saved["resume_data"], saved["projects_data"], saved["coursework_data"]]):
            raise HTTPException(status_code=404, detail="No career analysis yet — run an analysis first.")
        analysis = analyzer.full_analysis(
            saved["profile"] or StudentProfile(),
            saved["resume_data"],
            saved["projects_data"],
            saved["coursework_data"],
            saved["job_data"],
        )
        state["analysis"] = analysis
        _save(state)

    profile = analysis.get("profile") or {}
    gaps = analysis.get("gaps") or {"has": [], "improving": [], "missing": []}
    gaps_raw = analysis.get("gaps") or {"has": [], "improving": [], "missing": []}
    current = [h["skill"] for h in gaps.get("has", [])] + gaps_raw.get("extra_skills", [])
    skill_gaps = [i["skill"] for i in gaps.get("improving", [])] + [m["skill"] for m in gaps.get("missing", [])]
    return SkillGapsOut(
        target_role=profile.get("target_job_role", ""),
        current_skills=sorted(set(current)),
        skill_gaps=sorted(set(skill_gaps)),
    )


@router.post("/reset")
def reset_career() -> dict:
    with _lock:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        CAREER_STATE_FILE.write_text(
            json.dumps(dict(_DEFAULT), indent=2, ensure_ascii=False), encoding="utf-8"
        )
    return dict(_DEFAULT)
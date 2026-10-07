"""Optional AI refinement layer for the AI Career Analysis module (Person 1).

This module is a thin, swappable wrapper around the Gemini API. When
`GEMINI_API_KEY` is set it *refines* section extraction (resume, job
description); when it is missing or the call fails, every function returns
`None` and the deterministic engine in `analyzer.py` is used instead.

Nothing here is required for the module to work, and no secrets are
hardcoded — the API key comes from the shared `.env` via `app.config`.
"""

import asyncio
import json
import re
from typing import Optional

import httpx

from .. import config

API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent"
)

PROMPTS = {
    "resume": (
        "You are a resume parser for a student career platform. "
        "Return ONLY JSON of this shape: "
        '{"education": ["..."], "projects": ["..."], "experience": ["..."], '
        '"certifications": ["..."]}. '
        "Extract short factual bullet strings, no markdown."
    ),
    "job": (
        "You are a job description analyzer for a student career platform. "
        "Return ONLY JSON of this shape: "
        '{"required_skills": ["..."], "soft_skills": ["..."], '
        '"qualifications": ["..."], "technologies": ["..."]}. '
        "Extract exact phrases from the job description, no markdown."
    ),
}


async def _call(prompt: str, kind: str) -> Optional[dict]:
    if not config.GEMINI_API_KEY:
        return None
    url = API_URL.format(model=config.GEMINI_MODEL)
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": PROMPTS[kind]}]},
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json",
        },
    }
    data = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    url, params={"key": config.GEMINI_API_KEY}, json=payload
                )
            if resp.status_code in (429, 500, 503) and attempt < 2:
                await asyncio.sleep(2 * (attempt + 1))
                continue
            resp.raise_for_status()
            data = resp.json()
            break
        except (httpx.HTTPError, ValueError):
            if attempt < 2:
                await asyncio.sleep(2 * (attempt + 1))
                continue
            return None
    if data is None:
        return None
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return None
    return _extract_json(text)


def _extract_json(text: str) -> Optional[dict]:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None
        try:
            obj = json.loads(match.group(0))
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None


def _clean(value) -> list[str]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


async def refine_resume(content: str) -> Optional[dict]:
    """Best-effort AI section extraction. Returns None on failure/no key."""
    payload = {"resume": content[:12000]}
    result = await _call(
        f"Resume text:\n{json.dumps(payload, ensure_ascii=False)}\n\nParse it.", "resume"
    )
    if not result:
        return None
    return {
        "education": _clean(result.get("education")),
        "projects": _clean(result.get("projects")),
        "experience": _clean(result.get("experience")),
        "certifications": _clean(result.get("certifications")),
    }


async def refine_job(description: str) -> Optional[dict]:
    """Best-effort AI skill/qualification extraction. None on failure/no key."""
    result = await _call(
        f"Job description:\n{description[:12000]}\n\nAnalyze it.", "job"
    )
    if not result:
        return None
    return {
        "required_skills": _clean(result.get("required_skills")),
        "soft_skills": _clean(result.get("soft_skills")),
        "qualifications": _clean(result.get("qualifications")),
        "technologies": _clean(result.get("technologies")),
    }
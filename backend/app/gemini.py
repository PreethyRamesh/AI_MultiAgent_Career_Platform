import asyncio
import json
import re
from typing import Optional

import httpx

from . import config

API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent"
)

MENTOR_SYSTEM = (
    "You are an adaptive AI mentor inside a student career-preparation platform. "
    "You help students decide what to learn and do next. Be warm, concise "
    "(max 120 words), concrete and action-oriented. Prefer short lists or steps "
    "when useful. Reference the learner's roadmap context when provided. "
    "Never invent grades or credentials."
)

ROADMAP_SYSTEM = (
    "You are a career curriculum designer. Produce a personalized learning "
    "roadmap as strict JSON matching the schema given by the user. Use real, "
    "current resources (free or cheap when possible). No markdown, JSON only."
)


async def _call(prompt: str, system: str, json_mode: bool = False) -> Optional[str]:
    if not config.GEMINI_API_KEY:
        return None
    url = API_URL.format(model=config.GEMINI_MODEL)
    payload: dict = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system}]},
        "generationConfig": {"temperature": 0.6, "maxOutputTokens": 4096},
    }
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"
    data: dict | None = None
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
    return text.strip() or None


def extract_json(text: str) -> Optional[dict]:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


async def generate_roadmap_json(prompt: str) -> Optional[dict]:
    text = await _call(prompt, ROADMAP_SYSTEM, json_mode=True)
    if not text:
        return None
    return extract_json(text)


async def mentor_reply(prompt: str) -> Optional[str]:
    return await _call(prompt, MENTOR_SYSTEM)

from typing import Any

from .. import gemini
from ..models import Milestone, Phase, Roadmap


def _context(state: dict[str, Any]) -> str:
    roadmap_data = state.get("roadmap")
    if not roadmap_data:
        return "Learner has not generated a roadmap yet."
    roadmap = Roadmap(**roadmap_data)
    completed = set(state.get("completed", []))
    done_titles: list[str] = []
    next_ms: Milestone | None = None
    current_phase: Phase | None = None
    total = 0
    for phase in roadmap.phases:
        for ms in phase.milestones:
            total += 1
            if ms.id in completed:
                done_titles.append(ms.title)
            elif next_ms is None:
                next_ms = ms
                current_phase = phase
    pct = round(100 * len(completed) / total) if total else 0
    lines = [
        f"Target role: {roadmap.target_role}",
        f"Available time: {roadmap.hours_per_week} hours/week",
        f"Roadmap progress: {pct}% ({len(completed)}/{total} milestones)",
        f"Current skills: {', '.join(roadmap.current_skills) or 'not listed'}",
        f"Streak: {state.get('streak', 0)} days, XP: {state.get('xp', 0)}",
        f"Completed: {'; '.join(done_titles[-5:]) or 'none yet'}",
    ]
    if next_ms and current_phase:
        lines.append(
            f"Current phase: {current_phase.title} - next milestone: "
            f"{next_ms.title} ({next_ms.details})"
        )
    return "\n".join(lines)


FALLBACKS = [
    "Start with your next unlocked milestone — small, finished beats big and open. Which one feels heaviest? Tell me and we'll break it into 3 steps.",
    "Based on your roadmap, focus on one skill gap today for 45 focused minutes, then 15 minutes reviewing yesterday's notes. Consistency beats marathon sessions.",
    "Try the Feynman technique: explain the concept you're learning out loud in simple words. Where you stumble is exactly what to study next.",
    "Prioritize skills that appear in 3+ target job descriptions. Want to paste a job ad and I'll tell you which roadmap milestone maps to it?",
    "You're building evidence, not just knowledge. Ship one small artifact today — a snippet, a diagram, a short write-up — and add it to your portfolio.",
]


async def reply(state: dict[str, Any], message: str, history: list[dict]) -> tuple[str, str]:
    prompt = f"Learner context:\n{_context(state)}\n\n"
    if history:
        recent = history[-6:]
        prompt += "Recent conversation:\n"
        for turn in recent:
            role = turn.get("role", "user")
            prompt += f"{role}: {turn.get('content', '')}\n"
        prompt += "\n"
    prompt += f"Learner message: {message}\n\nReply as the mentor:"
    text = await gemini.mentor_reply(prompt)
    if text:
        return text, "gemini"
    msg = message.lower()
    if "job" in msg or "resume" in msg or "intern" in msg:
        return (
            "Map the job description to your roadmap: list its top 5 required "
            "skills, mark which milestones already cover them, then treat the "
            "uncovered ones as this week's missions. Share the role title and "
            "I'll suggest the order.",
            "fallback",
        )
    if "stuck" in msg or "difficult" in msg or "hard" in msg or "confused" in msg:
        return (
            "Stuck means the prerequisite is missing. 1) Re-read the last "
            "concept you understood fully. 2) Code/type one example from "
            "memory. 3) Search the exact error or concept for 10 minutes only. "
            "Still stuck? We downgrade the milestone into a smaller one.",
            "fallback",
        )
    if "plan" in msg or "today" in msg or "next" in msg:
        return (
            "Today's plan: 1) Complete your next unlocked mission (60-90 min), "
            "2) 20 min of active recall on yesterday's notes, 3) Log what you "
            "built. That's a streak day — do it before midnight.",
            "fallback",
        )
    return FALLBACKS[abs(hash(message)) % len(FALLBACKS)], "fallback"

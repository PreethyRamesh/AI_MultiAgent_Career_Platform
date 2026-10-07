import re
from datetime import datetime

from .. import gemini
from ..models import Milestone, Phase, ProfileIn, Resource, Roadmap

SCHEMA_HINT = """
Return ONLY JSON of this shape:
{
  "phases": [
    {
      "title": "string",
      "goal": "string",
      "duration": "e.g. 2 weeks",
      "milestones": [
        {
          "title": "string",
          "details": "1-2 sentences",
          "skills": ["skill", "..."],
          "resources": [{"title": "string", "url": "string"}],
          "xp": 50,
          "type": "learn | practice | build | review"
        }
      ]
    }
  ]
}
Rules: 3 to 5 phases, 3 to 5 milestones each, ordered from fundamentals to
job-ready. Prioritise the listed skill gaps. Milestones must be completable
in a few hours.
"""

RESOURCE_LIBRARY = [
    Resource(title="freeCodeCamp", url="https://www.freecodecamp.org"),
    Resource(title="MDN Web Docs", url="https://developer.mozilla.org"),
    Resource(title="Kaggle Learn", url="https://www.kaggle.com/learn"),
    Resource(title="roadmap.sh", url="https://roadmap.sh"),
    Resource(title="The Odin Project", url="https://www.theodinproject.com"),
    Resource(title="CS50 (Harvard, free)", url="https://cs50.harvard.edu"),
]

PHASE_TEMPLATES = [
    {
        "title": "Foundations",
        "goal": "Close the fundamentals gap so advanced topics click.",
        "duration": "2 weeks",
        "base": [
            ("Review core fundamentals", "Refresh the baseline concepts for your target role.", ["fundamentals"], "learn"),
            ("Fill prerequisite gaps", "Study the topics from your skill-gap list that block everything else.", ["gap-filling"], "learn"),
            ("Hands-on micro exercise", "Apply one concept end-to-end in a tiny exercise.", ["practice"], "practice"),
        ],
    },
    {
        "title": "Core Skills",
        "goal": "Build the primary skills the job description demands.",
        "duration": "3 weeks",
        "base": [
            ("Main skill deep-dive", "Work through a structured course on the highest-priority gap skill.", ["core-skill"], "learn"),
            ("Guided practice project", "Rebuild a small tutorial project without following along.", ["project"], "practice"),
            ("Pair skill up", "Combine two related skills in one small deliverable.", ["integration"], "build"),
        ],
    },
    {
        "title": "Applied Projects",
        "goal": "Produce portfolio evidence that proves the skills.",
        "duration": "3 weeks",
        "base": [
            ("Portfolio project v1", "Ship an end-to-end project that uses your target skills.", ["portfolio", "build"], "build"),
            ("Polish and document", "Add README, tests, and a short write-up of decisions.", ["documentation"], "review"),
            ("Simulate real work", "Replicate an industry-style constraint (deadlines, review, refactor).", ["engineering"], "practice"),
        ],
    },
    {
        "title": "Job Readiness",
        "goal": "Translate skills into interview and application performance.",
        "duration": "2 weeks",
        "base": [
            ("Target 5 job descriptions", "Extract repeated requirements and confirm roadmap coverage.", ["jd-analysis"], "review"),
            ("Interview drills", "Practice common questions for your target role aloud or in writing.", ["interview"], "practice"),
            ("Resume & profile update", "Rewrite bullets to quantify the projects you just shipped.", ["communication"], "review"),
        ],
    },
]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "item"


def _fallback(profile: ProfileIn) -> Roadmap:
    gaps = profile.skill_gaps or profile.current_skills or ["core skills"]
    phases: list[Phase] = []
    for i, template in enumerate(PHASE_TEMPLATES):
        milestones: list[Milestone] = []
        for j, (title, details, skills, mtype) in enumerate(template["base"]):
            mid = f"p{i}-m{j}"
            tag = gaps[(i + j) % len(gaps)]
            milestones.append(
                Milestone(
                    id=mid,
                    title=title,
                    details=f"{details} Focus skill: {tag}.",
                    skills=[tag] + list(skills),
                    resources=[RESOURCE_LIBRARY[(i + j) % len(RESOURCE_LIBRARY)]],
                    xp=40 + 10 * j,
                    type=mtype,
                )
            )
        phases.append(
            Phase(
                id=f"p{i}",
                title=template["title"],
                goal=template["goal"],
                duration=template["duration"],
                milestones=milestones,
            )
        )
    return Roadmap(
        target_role=profile.target_role,
        hours_per_week=profile.hours_per_week,
        current_skills=profile.current_skills,
        phases=phases,
    )


def _parse_generated(data: dict, profile: ProfileIn) -> Roadmap:
    phases: list[Phase] = []
    raw_phases = data.get("phases", [])
    if not isinstance(raw_phases, list) or not raw_phases:
        raise ValueError("no phases")
    for i, rp in enumerate(raw_phases[:6]):
        milestones: list[Milestone] = []
        for j, rm in enumerate(rp.get("milestones", [])[:6]):
            resources = []
            for r in rm.get("resources", [])[:3]:
                if isinstance(r, dict) and r.get("title"):
                    resources.append(
                        Resource(title=str(r["title"]), url=str(r.get("url", "")))
                    )
            milestones.append(
                Milestone(
                    id=f"p{i}-m{j}",
                    title=str(rm.get("title", f"Milestone {j + 1}")),
                    details=str(rm.get("details", "")),
                    skills=[str(s) for s in rm.get("skills", []) if s],
                    resources=resources or RESOURCE_LIBRARY[:1],
                    xp=int(rm.get("xp", 50) or 50),
                    type=str(rm.get("type", "learn"))
                    if rm.get("type") in ("learn", "practice", "build", "review")
                    else "learn",
                )
            )
        if not milestones:
            continue
        phases.append(
            Phase(
                id=f"p{i}",
                title=str(rp.get("title", f"Phase {i + 1}")),
                goal=str(rp.get("goal", "")),
                duration=str(rp.get("duration", "")),
                milestones=milestones,
            )
        )
    if not phases:
        raise ValueError("empty roadmap")
    return Roadmap(
        target_role=profile.target_role,
        hours_per_week=profile.hours_per_week,
        current_skills=profile.current_skills,
        phases=phases,
    )


async def build(profile: ProfileIn) -> tuple[Roadmap, str]:
    prompt = (
        f"Target role: {profile.target_role}\n"
        f"Current skills: {', '.join(profile.current_skills) or 'beginner'}\n"
        f"Known skill gaps: {', '.join(profile.skill_gaps) or 'unknown - infer from role'}\n"
        f"Available time: {profile.hours_per_week} hours per week\n"
        f"Today's date: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        f"Schema:{SCHEMA_HINT}"
    )
    data = await gemini.generate_roadmap_json(prompt)
    if data:
        try:
            return _parse_generated(data, profile), "gemini"
        except (ValueError, TypeError, KeyError):
            pass
    return _fallback(profile), "fallback"

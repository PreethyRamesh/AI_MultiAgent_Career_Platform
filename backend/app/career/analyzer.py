"""Deterministic analysis engine for the AI Career Analysis module (Person 1).

Implements the full career-analysis pipeline with clearly separated, pure
functions so a real AI service can be plugged in later (see `ai.py`):

  1. Profile & Goal Setup      – profile normalization
  2. Resume Analysis           – section parsing + skill extraction
  3. Project Analysis          – skills demonstrated per project
  4. Coursework Analysis       – skills gained from each course
  5. AI Skill Assessment       – categorized skill profile + strengths
  6. Target Job Analysis       – required skills / qualifications / tech
  7. Skill Gap Analysis        – has / improving / missing
  8. Job Match Score           – 0-100 score + factors
  9. Career Recommendations    – suitable roles + reasons
  10. Skill-to-Job Mapping     – requirement -> satisfying skills
"""

import re
from typing import Optional

from . import knowledge as kb
from .models import CourseworkIn, JobIn, ProjectsIn, ResumeIn, StudentProfile

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _canonical(current: list[str]) -> list[dict]:
    """Map a raw skill list to {name, category}; unknown skills -> 'Other'."""
    out: list[dict] = []
    seen: set[str] = set()
    for raw in current:
        name = raw.strip()
        if not name:
            continue
        key = kb.canonicalize(name) or name
        if key in seen:
            continue
        seen.add(key)
        meta = kb.SKILLS.get(key)
        out.append({"name": key, "category": meta["category"] if meta else "Other"})
    return out


# ---------------------------------------------------------------------------
# 2. Resume Analysis
# ---------------------------------------------------------------------------

def parse_resume(content: str) -> dict:
    """Split resume text into sections and extract structured evidence."""
    sections: dict[str, list[str]] = {}
    order: list[str] = []
    current = "summary"
    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue
        section = kb.is_section_header(line)
        if section:
            current = section
            if section not in sections:
                sections[section] = []
                order.append(section)
        else:
            sections.setdefault(current, []).append(line)

    all_lines = [ln for lines in sections.values() for ln in lines]

    def section_lines(name: str) -> list[str]:
        return sections.get(name, [])

    # Education: explicit section, plus any degree-like lines anywhere.
    education: list[str] = []
    for line in section_lines("education"):
        if line and line not in education:
            education.append(line)
    for line in all_lines:
        if line in education:
            continue
        # degree tokens ignore punctuation/spacing: "B.E." -> "be"
        compact = re.sub(r"[^a-z0-9]+", "", line.lower())
        if any(k in compact for k in kb.DEGREE_KEYWORDS):
            education.append(line)

    # Projects: explicit section + project-keyword lines elsewhere.
    projects: list[str] = []
    for line in section_lines("projects"):
        if line and line not in projects:
            projects.append(line)
    for line in all_lines:
        if line in projects:
            continue
        nl = kb.normalize(line)
        if any(k in nl for k in kb.PROJECT_KEYWORDS) and len(line) > 12:
            projects.append(line)

    # Experience / internships.
    experience: list[str] = []
    for line in section_lines("experience"):
        if line and line not in experience:
            experience.append(line)
    for line in all_lines:
        if line in experience:
            continue
        nl = kb.normalize(line)
        if any(k in nl for k in kb.EXPERIENCE_KEYWORDS) and len(line) > 12:
            experience.append(line)

    # Certifications.
    certifications: list[str] = []
    for line in section_lines("certifications"):
        if line and line not in certifications:
            certifications.append(line)
    for line in all_lines:
        if line in certifications:
            continue
        nl = kb.normalize(line)
        if any(k in nl for k in kb.CERT_KEYWORDS):
            certifications.append(line)

    # Skill matching with source sections for evidence tagging.
    matched: dict[str, dict] = {}
    for section, lines in sections.items():
        text = "\n".join(lines)
        for name, hit in kb.match_skills(text).items():
            entry = matched.setdefault(name, {"name": name, "category": hit["category"], "count": 0, "sources": []})
            entry["count"] += hit["count"]
            entry["sources"].append(section)
    # guarantee every hit in the full text is present
    for name, hit in kb.match_skills(content).items():
        entry = matched.setdefault(name, {"name": name, "category": hit["category"], "count": 0, "sources": []})
        entry["count"] = max(entry["count"], hit["count"])
        if entry["sources"] == ["summary"] and "summary" not in entry["sources"]:
            pass  # summary default is fine

    matched_skills = sorted(matched.values(), key=lambda s: -s["count"])

    return {
        "education": education,
        "projects": projects,
        "experience": experience,
        "certifications": certifications,
        "matched_skills": matched_skills,
        "sections": sections,
    }


def analyze_resume(resume: ResumeIn) -> dict:
    data = parse_resume(resume.content)
    data["ai_source"] = "fallback"
    return data


# ---------------------------------------------------------------------------
# 3. Project Analysis
# ---------------------------------------------------------------------------

def analyze_projects(payload: ProjectsIn) -> dict:
    results = []
    all_skills: set[str] = set()
    for p in payload.projects:
        text = f"{p.title}\n{p.description}"
        hits = kb.match_skills(text)
        detail = [
            {"name": name, "category": v["category"], "count": v["count"]}
            for name, v in sorted(hits.items(), key=lambda kv: -kv[1]["count"])
        ]
        skills = [d["name"] for d in detail]
        all_skills.update(skills)
        summary = ""
        if detail:
            top = ", ".join(skills[:4])
            summary = (
                f"Demonstrates {top}"
                + (" and more." if len(skills) > 4 else ".")
            )
        results.append(
            {
                "title": p.title,
                "description": p.description,
                "skills": skills,
                "skills_detail": detail,
                "summary": summary,
            }
        )
    return {"projects": results, "all_skills": sorted(all_skills)}


# ---------------------------------------------------------------------------
# 4. Coursework Analysis
# ---------------------------------------------------------------------------

def analyze_coursework(payload: CourseworkIn) -> dict:
    results = []
    all_skills: set[str] = set()
    for c in payload.courses:
        mapped = kb.match_course(c.name)
        # also match any skills described in the description
        extra = [n for n in kb.match_skills(c.description) if n not in mapped]
        skills = list(dict.fromkeys(mapped + extra))
        all_skills.update(skills)
        results.append({"name": c.name, "skills": skills})
    return {"courses": results, "all_skills": sorted(all_skills)}


# ---------------------------------------------------------------------------
# 5. AI Skill Assessment
# ---------------------------------------------------------------------------

def _evidence_weights(resume_data: Optional[dict], projects_data: Optional[dict], coursework_data: Optional[dict]) -> dict:
    """Canonical skill -> list[(type, label, weight)] evidence."""
    evidence: dict[str, list] = {}

    def add(skill: str, etype: str, label: str, weight: int) -> None:
        evidence.setdefault(skill, []).append((etype, label, weight))

    resume = resume_data or {}
    for s in resume.get("matched_skills", []):
        name = s["name"]
        sources = s.get("sources") or []
        weight = 1
        if "skills" in sources:
            weight += 1
        if "certifications" in sources:
            weight += 1
        label = f"Resume · {', '.join(sources) or 'mentioned'}"
        add(name, "resume", label, weight)

    projects = projects_data or {}
    for p in projects.get("projects", []):
        title = p.get("title") or "Project"
        for s in p.get("skills", []):
            add(s, "project", f"Project · {title}", 2)

    courses = coursework_data or {}
    for c in courses.get("courses", []):
        name = c.get("name") or "Course"
        for s in c.get("skills", []):
            weight = 2 if ("advanced" in kb.normalize(name) or "lab" in kb.normalize(name)) else 1
            add(s, "coursework", f"Coursework · {name}", weight)

    return evidence


def build_assessment(
    profile: StudentProfile,
    resume_data: Optional[dict] = None,
    projects_data: Optional[dict] = None,
    coursework_data: Optional[dict] = None,
) -> dict:
    evidence = _evidence_weights(resume_data, projects_data, coursework_data)

    # Declared skills are strong evidence of current ability.
    for item in _canonical(profile.current_skills):
        evidence.setdefault(item["name"], []).append(("profile", "Declared in profile", 3))

    skills: list[dict] = []
    for name, entries in evidence.items():
        unique = {(t, label): w for (t, label, w) in entries}
        total = sum(unique.values())
        level = min(5, 1 + total)
        meta = kb.SKILLS.get(name)
        skills.append(
            {
                "skill": name,
                "category": meta["category"] if meta else "Other",
                "level": level,
                "status": "has" if level >= 3 else "improving",
                "sources": [
                    {"type": t, "label": label, "weight": w} for (t, label), w in unique.items()
                ],
            }
        )

    skills.sort(key=lambda s: (-s["level"], s["skill"]))

    strengths = [s for s in skills if s["status"] == "has"]
    has_names = {s["skill"] for s in skills if s["status"] == "has"}

    # Category breakdown.
    buckets: dict[str, list[dict]] = {}
    for s in skills:
        buckets.setdefault(s["category"], []).append(s)
    categories = []
    for cat in kb.SKILL_CATEGORIES:
        items = buckets.get(cat, [])
        if not items:
            continue
        level_total = sum(i["level"] for i in items)
        avg = level_total / len(items)
        categories.append(
            {
                "category": cat,
                "skill_count": len(items),
                "level_total": level_total,
                "avg_level": round(avg, 2),
                "pct": round(100 * avg / 5, 1),
                "skills": [i["skill"] for i in sorted(items, key=lambda i: -i["level"])],
            }
        )
    categories.sort(key=lambda c: -c["level_total"])

    summary = {
        "total_skills": len(skills),
        "has_count": len(strengths),
        "improving_count": len(skills) - len(strengths),
        "top_categories": [c["category"] for c in categories[:3]],
        "strongest": strengths[0]["skill"] if strengths else "",
    }

    return {
        "skills": skills,
        "categories": categories,
        "strengths": strengths,
        "summary": summary,
        "profile_has_count": len(has_names),
    }


# ---------------------------------------------------------------------------
# 6. Target Job Analysis
# ---------------------------------------------------------------------------

_JOB_QUAL_RE = [
    r"\b\d+\s*\+?\s*(?:-\s*\d+\s*)?years?(?:\s+of)?\s+experience\b",
    r"\b(?:bachelor(?:'s)?|master(?:'s)?|ph\.?d|b\.?tech|m\.?tech|b\.?e|b\.?sc|m\.?sc|mba|mca|bca|bcom|mcom|bba)\b",
    r"\bfresher\b|\bentry[- ]level\b",
]


def analyze_job(job: JobIn) -> dict:
    text = job.description
    hits = kb.match_skills(text)
    entries = [
        {"name": name, "category": v["category"], "count": v["count"]}
        for name, v in sorted(hits.items(), key=lambda kv: -kv[1]["count"])
    ]
    required_skills = [e for e in entries if e["category"] != "Soft Skills"]
    soft_skills = [e for e in entries if e["category"] == "Soft Skills"]

    quals: list[str] = []
    for pat in _JOB_QUAL_RE:
        for m in re.finditer(pat, text, re.I):
            snippet = m.group(0).strip()
            if snippet and snippet not in quals:
                quals.append(snippet)
    if not quals:
        quals = []

    title_hint = job.title.strip() or (text.strip().splitlines()[0][:80] if text.strip() else "")

    return {
        "title_hint": title_hint,
        "required_skills": required_skills,
        "soft_skills": soft_skills,
        "qualifications": quals,
        "technologies": [e["name"] for e in required_skills],
        "ai_source": "fallback",
    }


# ---------------------------------------------------------------------------
# 7. Skill Gap Analysis
# ---------------------------------------------------------------------------

def build_gap_report(assessment: dict, job: dict) -> dict:
    profile = {s["skill"]: s for s in assessment.get("skills", [])}
    required = job.get("required_skills", []) + job.get("soft_skills", [])

    has_items, improving_items, missing_items = [], [], []
    for req in required:
        name = req["name"]
        entry = profile.get(name)
        item = {
            "skill": name,
            "category": req.get("category", "Other"),
            "level": entry["level"] if entry else 0,
            "in_job_note": f"Requested {req.get('count', 1)}× in the job description",
        }
        if entry and entry["status"] == "has":
            has_items.append(item)
        elif entry:
            improving_items.append(item)
        else:
            missing_items.append(item)

    required_names = {r["name"] for r in required}
    extra_skills = [s["skill"] for s in assessment.get("skills", []) if s["skill"] not in required_names]

    return {
        "has": has_items,
        "improving": improving_items,
        "missing": missing_items,
        "extra_skills": extra_skills,
    }


# ---------------------------------------------------------------------------
# 8. Job Match Score
# ---------------------------------------------------------------------------

def compute_match(assessment: dict, job: dict, gap: dict) -> dict:
    required_tech = [r for r in job.get("required_skills", []) if r["category"] != "Soft Skills"]
    required_soft = job.get("soft_skills", [])
    profile = {s["skill"]: s for s in assessment.get("skills", [])}

    has = list(gap.get("has", []))
    improving = list(gap.get("improving", []))
    missing = list(gap.get("missing", []))
    missing_names = {m["skill"] for m in missing}

    covered_tech = len(has) + 0.5 * len(improving)
    coverage = covered_tech / len(required_tech) if required_tech else 1.0

    soft_covered = sum(
        1.0 if (profile.get(r["name"]) or {}).get("status") == "has"
        else 0.5 if (profile.get(r["name"]) or {}).get("status") == "improving"
        else 0.0
        for r in required_soft
    )
    soft_coverage = soft_covered / len(required_soft) if required_soft else 1.0

    matched_levels = []
    for r in required_tech:
        entry = profile.get(r["name"])
        if entry and entry["status"] == "has":
            matched_levels.append(entry["level"])
        elif entry:
            matched_levels.append(entry["level"] * 0.5)
    strength = (sum(matched_levels) / (5 * len(matched_levels))) if matched_levels else 0.0

    extra_bonus = min(1.0, len(gap.get("extra_skills", [])) / 5.0)

    score = round(
        100 * (0.55 * coverage + 0.15 * soft_coverage + 0.20 * strength + 0.10 * extra_bonus)
    ) if required_tech else 0
    score = max(0, min(100, score))

    if score >= 80:
        grade = "Excellent"
    elif score >= 60:
        grade = "Good"
    elif score >= 40:
        grade = "Needs Work"
    else:
        grade = "Low"

    factors = [
        {"name": "Technical skill coverage", "weight": 0.55, "value": round(coverage, 2), "impact": "positive" if coverage >= 0.5 else "negative"},
        {"name": "Soft skill coverage", "weight": 0.15, "value": round(soft_coverage, 2), "impact": "positive" if soft_coverage >= 0.5 else "negative"},
        {"name": "Skill strength", "weight": 0.20, "value": round(strength, 2), "impact": "positive" if strength >= 0.5 else "negative"},
        {"name": "Bonus skills beyond the job", "weight": 0.10, "value": round(extra_bonus, 2), "impact": "positive"},
    ]

    return {
        "score": score,
        "grade": grade,
        "factors": factors,
        "matched_skills": [h["skill"] for h in has],
        "improving_skills": [i["skill"] for i in improving],
        "missing_skills": sorted(missing_names),
        "covered": len(has) + len(improving),
        "total_required": len(required_tech),
    }


# ---------------------------------------------------------------------------
# 9. Career Recommendations
# ---------------------------------------------------------------------------

def recommend_roles(profile: StudentProfile, assessment: dict) -> list:
    profile_map = {s["skill"]: s for s in assessment.get("skills", [])}
    target = kb.normalize(profile.target_job_role)

    out = []
    for role in kb.ROLES:
        matched, missing = [], []
        score = 0.0
        for req in role["required"]:
            entry = profile_map.get(req)
            if entry and entry["status"] == "has":
                score += 1.0
                matched.append(req)
            elif entry:
                score += 0.5
                matched.append(req)
            else:
                missing.append(req)
        pct = round(100 * score / max(1, len(role["required"])))
        goal_match = bool(target) and (target in kb.normalize(role["role"]) or kb.normalize(role["role"]) in target)
        if goal_match:
            pct = min(100, pct + 8)
        out.append(
            {
                "role": role["role"],
                "summary": role["summary"],
                "match_pct": pct,
                "matched": matched,
                "missing": missing,
                "goal_match": goal_match,
            }
        )

    out.sort(key=lambda r: (-r["match_pct"], len(r["matched"])))
    return out[:5]


# ---------------------------------------------------------------------------
# 10. Skill-to-Job Mapping
# ---------------------------------------------------------------------------

def build_mapping(job: dict, gap: dict, assessment: dict) -> dict:
    profile = {s["skill"]: s for s in assessment.get("skills", [])}
    required = job.get("required_skills", []) + job.get("soft_skills", [])

    mappings = []
    seen = set()
    for req in required:
        name = req["name"]
        if name in seen:
            continue
        seen.add(name)
        entry = profile.get(name)
        if entry:
            status = entry["status"]
            sources = sorted(entry.get("sources", []), key=lambda s: -s.get("weight", 0))[:3]
            note = "Satisfied by your profile." if status == "has" else "Partial coverage — strengthen with projects or advanced courses."
        else:
            status = "missing"
            sources = []
            note = "No evidence yet — add a course, project or certification covering this skill."
        mappings.append(
            {"requirement": name, "category": req.get("category", "Other"), "status": status, "satisfied_by": sources, "note": note}
        )

    missing_requirements = [m["requirement"] for m in mappings if m["status"] == "missing"]
    return {
        "mappings": mappings,
        "covered": len(mappings) - len(missing_requirements),
        "missing": len(missing_requirements),
        "missing_requirements": missing_requirements,
    }


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def full_analysis(
    profile: StudentProfile,
    resume_data: Optional[dict] = None,
    projects_data: Optional[dict] = None,
    coursework_data: Optional[dict] = None,
    job_data: Optional[dict] = None,
) -> dict:
    assessment = None
    if profile or resume_data or projects_data or coursework_data:
        assessment = build_assessment(profile, resume_data, projects_data, coursework_data)

    gaps = build_gap_report(assessment or {"skills": []}, job_data or {"required_skills": [], "soft_skills": []}) if job_data else None
    match = compute_match(assessment or {"skills": []}, job_data or {"required_skills": []}, gaps or {"has": [], "improving": [], "missing": [], "extra_skills": []}) if job_data else None
    mapping = build_mapping(job_data or {"required_skills": [], "soft_skills": []}, gaps or {"has": [], "improving": [], "missing": []}, assessment or {"skills": []}) if job_data else None
    recommendations = recommend_roles(profile, assessment or {"skills": []}) if assessment else []

    return {
        "profile": profile.model_dump() if profile else None,
        "assessment": assessment,
        "job": job_data,
        "gaps": gaps,
        "match": match,
        "recommendations": recommendations,
        "mapping": mapping,
    }
# AI Skill-Gap Analysis & Development Roadmap Platform

**Problem Statement 6:** Build an AI platform that analyzes a student's skills, projects, coursework and target job descriptions to identify skill gaps and generate a personalized development roadmap.

## Core Features

1. **Job-Description Analysis** – Parse and analyze target job descriptions to extract required skills, seniority, and role expectations.
2. **Resume / Project Analysis** – Analyze resumes, coursework, and project portfolios.
3. **Skill Extraction & Identification** – Extract candidate skills and map them against job requirements.
4. **Skill-Gap Identification** – Compute gaps between current skills and target role requirements.
5. **Learning Roadmap Generation** – Generate a personalized, prioritized development roadmap with resources.
6. **Progress Tracking** – Track roadmap completion and evolving skill coverage over time.

## Team Branches

| Branch | Owner | Role | Focus Area |
|---|---|---|---|
| `person1-preethy` | Preethy | 👤 AI Career Analysis | Profile & goal setup, AI skill assessment, skill-gap analysis, career recommendations |
| `person2-sandhiya` | Sandhiya | 🤖 AI Learning & Guidance | AI learning roadmap, daily mission system, adaptive AI mentor, skill tree |
| `person3-monika` | Monika | 📊 Progress & Product | Dashboard, streak & gamification, analytics & graphs, achievements |

### Responsibilities

**Person 1 — AI Career Analysis:** Understand the student and identify where they stand.

**Person 2 — AI Learning & Guidance:** Decide what the student should learn and do next.

**Person 3 — Progress & Product:** Visualize and motivate progress.

## Getting Started

```bash
git clone <repo-url>
git checkout person1-preethy   # or person2-sandhiya / person3-monika
```

## AI Career Analysis Module (Person 1)

Built on top of the shared FastAPI + Jinja2 + vanilla JS/CSS stack. Served at
**`/career`**; API under **`/api/career/*`**. Adds:

- Profile & Goal Setup, Resume / Project / Coursework Analysis
- AI Skill Assessment (categorized skill profile + strengths)
- Target Job Analysis, Skill Gap Analysis (has / improving / missing)
- Job Match Score (0–100 with factors), Career Recommendations, Skill→Job Mapping

Integration contract: `POST /api/career/skill-gaps` publishes gaps for Person 2's
`POST /api/roadmap`; `GET /api/career/state` exposes match/assessment data for
Person 3's dashboard. See `backend/career/README.md` for details.

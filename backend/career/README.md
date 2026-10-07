# AI Career Analysis Module (Person 1 — `person1-preethy`)

Understands the student: profile & goals, resume/project/coursework parsing,
AI skill assessment, target-job analysis, skill-gap analysis, job match score,
career recommendations and skill→job mapping.

Stack: same as the rest of the platform — FastAPI + Jinja2 + vanilla JS/CSS.
The page is served at **`/career`** and reuses the shared `static/style.css`
design tokens (`career.css` only *adds* module components).

## Run

```bash
cd backend
uvicorn app.main:app --reload     # open http://127.0.0.1:8000/career
python smoke_career_test.py        # hermetic end-to-end test (no API key needed)
```

## Height-map of the module

| Path | Purpose |
|---|---|
| `app/career/knowledge.py` | Skill taxonomy, aliases, course→skills, role→skills, resume heuristics |
| `app/career/analyzer.py` | Deterministic engine (works with **no API key**; the fallback) |
| `app/career/ai.py` | Optional Gemini refinement (auto-disabled without `GEMINI_API_KEY`) |
| `app/career/router.py` | `APIRouter` + state in `app/data/career_state.json` (separate from P2's `state.json`) |
| `static/career.js` / `career.css` / `templates/career.html` | Dashboard UI |

## API

| Method | Path | Description |
|---|---|---|
| GET | `/career` | Career Analysis dashboard page |
| GET | `/api/career/state` | Saved profile + results |
| POST | `/api/career/profile` | Save `{name, degree, year_of_study, current_skills[], target_job_role, career_goal}` |
| POST | `/api/career/resume` | `{content}` → education/projects/experience/certs + extracted skills |
| POST | `/api/career/projects` | `{projects:[{title, description}]}` → skills per project |
| POST | `/api/career/coursework` | `{courses:[{name, description}]}` → skills per subject |
| POST | `/api/career/job` | `{title?, description}` → required skills / soft skills / qualifications / tech |
| POST | `/api/career/analyze` | Full pipeline → assessment + gaps + match + recommendations + mapping |
| POST | `/api/career/skill-gaps` | `{target_role, current_skills[], skill_gaps[]}` — **Person 2 integration** |
| POST | `/api/career/reset` | Clear module state |

## Integration notes for teammates

- **Person 2 (Learning/Roadmap):** call `POST /api/career/skill-gaps`, then feed the
  response straight into `POST /api/roadmap` as `{target_role, current_skills,
  skill_gaps, hours_per_week}`. The module's UI already does this via the
  “Send skill gaps to Learning Roadmap” button.
- **Person 3 (Dashboard/Progress):** `GET /api/career/state` exposes
  `analysis.match.score`, `analysis.assessment.summary` and gap counts for widgets.
- **Swapping in real AI:** the deterministic engine is the default. Set
  `GEMINI_API_KEY` in `backend/.env` and `ai.py` refines extraction; extend
  `ai.refine_resume` / `ai.refine_job` for richer prompts. No keys are ever
  hardcoded.
- **Dependencies:** none beyond the shared `requirements.txt`.
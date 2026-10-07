# AI Learning & Guidance Module (Person 2 — person2-sandhiya)

FastAPI + Jinja2 module providing the learning side of the platform:

- **AI Learning Roadmap** — Gemini-generated, multi-phase plan with milestones, skills and resources (smart template fallback when no API key).
- **Daily Mission System** — a short, completable mission list derived from the roadmap, with XP.
- **Skill Tree** — milestones rendered as a per-phase tree with locked / available / unlocked states.
- **Adaptive AI Mentor** — context-aware chat that knows your progress, phase and streak.
- **Progress tracking** — XP, level, streak and completion %.

## Run

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env      # add your GEMINI_API_KEY (optional; fallback works without it)
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/roadmap` | Generate roadmap `{target_role, current_skills, skill_gaps, hours_per_week}` |
| GET | `/api/state` | Full app state (roadmap, missions, progress, tree, mentor history) |
| GET | `/api/missions/today` | Today's missions |
| POST | `/api/missions/complete` | Complete a mission `{item_id}` |
| GET | `/api/skill-tree` | Current skill tree |
| POST | `/api/mentor` | Chat `{message, history}` |
| POST | `/api/reset` | Reset progress |

## Integrating with Person 1 / Person 3

- Person 1 (Career Analysis) should publish the skill-gap list to `POST /api/roadmap` as `skill_gaps`.
- Person 3 (Dashboard) can consume `GET /api/state` for XP, streak, and completion metrics.

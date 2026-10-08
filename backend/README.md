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

Pages `/` (Learning Hub) and `/career` (Career Analysis) are **auth-protected** — unauthenticated
visitors are redirected to `/login`.

## Authentication (mock backend, swappable)

Login / Sign Up / Forgot password pages ship with the module. Auth logic lives in
`backend/app/auth.py` entirely (file-backed users + sessions, PBKDF2 password hashing,
HttpOnly session cookie). Routes only call this module, so a real backend (DB/OAuth/JWT)
can replace it without touching any UI.

| Page / API | Description |
|---|---|
| `GET /login` `GET /signup` `GET /forgot` | Auth pages |
| `POST /api/auth/login` | `{email, password, remember}` → sets session cookie |
| `POST /api/auth/signup` | `{full_name, email, password}` → creates account + login |
| `POST /api/auth/forgot` | Mock — honest message, no email is sent |
| `GET /api/auth/me` | Current user or `401` |
| `POST /logout` | Clears session and cookie |

User/session data is stored in `app/data/users.json` / `sessions.json` (gitignored).

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

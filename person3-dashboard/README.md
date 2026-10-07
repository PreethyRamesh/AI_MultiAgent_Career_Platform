# Person 3 — Monika | Progress & Product

Professional FastAPI + Jinja2 + Chart.js implementation.

## Includes
- Dashboard: role, completion %, XP, level, streak, next mission
- Gamification: XP/level/streak/badges
- Analytics: skill coverage vs target, phase progress over time, hours invested
- Daily progress snapshots
- Progress history API
- Achievement engine
- First Mission
- 7-Day Streak
- Phase Complete
- Roadmap 50%
- Responsive colorful professional UI

## Ownership
Person 2 owns:
- GET /api/state
- POST /api/missions/complete

Person 3 consumes /api/state and does not duplicate mission/XP/streak logic.

Person 3 owns:
- POST /api/progress/snapshot
- GET /api/progress/history
- GET /api/achievements
- POST /api/achievements/evaluate

## Run immediately
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

Open http://127.0.0.1:8001/dashboard

Analytics: http://127.0.0.1:8001/analytics
API docs: http://127.0.0.1:8001/docs

The package defaults to DEMO_MODE=true so it can be presented immediately.

## Integrate with Person 2
Set:
DEMO_MODE=false
STATE_API_BASE_URL=http://127.0.0.1:8000

Then run Person 3 on port 8001:
```bash
uvicorn main:app --reload --port 8001
```

Person 2 remains the source of truth for current progress.

## Expected state contract
```json
{
  "role": "Data Scientist",
  "roadmap": [],
  "missions": [
    {"id": 1, "title": "Train Model", "completed": false, "phase": 2}
  ],
  "progress": {
    "xp": 750,
    "level": 4,
    "streak": 7,
    "completion_pct": 52
  },
  "skill_tree": [
    {"name": "Python", "current": 82, "target": 90}
  ]
}
```

## Daily snapshots
Dashboard/analytics automatically call:
POST /api/progress/snapshot

Snapshots are unique per user/day and are updated rather than duplicated.

## Git
```bash
git checkout person3-monika
git add .
git commit -m "Implement Person 3 progress analytics and achievements"
git push origin person3-monika
```

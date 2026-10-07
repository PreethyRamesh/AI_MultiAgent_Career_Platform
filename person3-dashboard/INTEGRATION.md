# Person 3 Integration Contract

## Person 2 owns
GET /api/state
POST /api/missions/complete

Do not recreate XP, level, streak or mission-completion logic.

## Person 3 owns
POST /api/progress/snapshot
GET /api/progress/history
GET /api/achievements
POST /api/achievements/evaluate

## Skill contract
Each skill may look like:
{"name":"Python","current":82,"target":90}

Common alternatives accepted:
- skill instead of name
- coverage/progress instead of current
- target_pct instead of target

## Mission contract
{"id":1,"title":"Train Model","completed":false,"phase":2}

An explicit roadmap item with phase_complete=true is also supported.

## User ID
The demo uses demo-user. Replace this with the authenticated user's stable
ID when integrating into the real application.

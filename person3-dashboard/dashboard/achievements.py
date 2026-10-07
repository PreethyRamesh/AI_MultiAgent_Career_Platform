from .database import award_achievement, get_achievements

ACHIEVEMENT_DEFINITIONS = [
    {"key":"first_mission","name":"First Mission",
     "description":"Complete your first mission.","icon":"🎯"},
    {"key":"seven_day_streak","name":"7-Day Streak",
     "description":"Maintain a 7-day learning streak.","icon":"🔥"},
    {"key":"phase_complete","name":"Phase Complete",
     "description":"Complete an entire roadmap phase.","icon":"🏁"},
    {"key":"roadmap_50","name":"Roadmap 50%",
     "description":"Reach at least 50% roadmap completion.","icon":"🏆"}
]

def completed_missions(state):
    return sum(1 for m in state.get("missions", []) if m.get("completed") is True)

def phase_is_complete(state):
    for item in state.get("roadmap", []):
        if isinstance(item, dict) and item.get("phase_complete") is True:
            return True
    phases = {}
    for mission in state.get("missions", []):
        if not isinstance(mission, dict) or mission.get("phase") is None:
            continue
        phases.setdefault(str(mission["phase"]), []).append(mission)
    return any(items and all(m.get("completed") is True for m in items)
               for items in phases.values())

def evaluate_and_award(user_id, state):
    p = state.get("progress", {})
    conditions = {
        "first_mission": completed_missions(state) >= 1,
        "seven_day_streak": p.get("streak", 0) >= 7,
        "phase_complete": phase_is_complete(state),
        "roadmap_50": p.get("completion_pct", 0) >= 50
    }
    newly = []
    for item in ACHIEVEMENT_DEFINITIONS:
        if conditions[item["key"]]:
            if award_achievement(user_id, item["key"], item["name"],
                                 item["description"], item["icon"]):
                newly.append(item["key"])
    return newly

def achievement_view(user_id):
    earned = get_achievements(user_id)
    earned_keys = {x["achievement_key"] for x in earned}
    return [
        {
            **definition,
            "earned": definition["key"] in earned_keys,
            "earned_at": next(
                (x["earned_at"] for x in earned
                 if x["achievement_key"] == definition["key"]), None
            )
        }
        for definition in ACHIEVEMENT_DEFINITIONS
    ]

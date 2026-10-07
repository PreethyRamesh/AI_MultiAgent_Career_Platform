from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)

r = c.get("/")
assert r.status_code == 200, r.text

r = c.post(
    "/api/roadmap",
    json={
        "target_role": "Frontend Developer",
        "current_skills": ["HTML", "CSS"],
        "skill_gaps": ["JavaScript", "React", "Git"],
        "hours_per_week": 8,
    },
)
assert r.status_code == 200, r.text
data = r.json()
print("roadmap source:", data["source"], "phases:", len(data["roadmap"]["phases"]))
assert data["progress"]["roadmap_ready"]

r = c.get("/api/missions/today")
assert r.status_code == 200, r.text
day = r.json()
print("missions today:", len(day["items"]))
assert day["items"], "expected missions"

item_id = day["items"][0]["id"]
r = c.post("/api/missions/complete", json={"item_id": item_id})
assert r.status_code == 200, r.text
prog = r.json()["progress"]
print("after complete -> xp:", prog["xp"], "streak:", prog["streak"], "pct:", prog["completion_pct"])
assert prog["xp"] > 0 and prog["streak"] >= 1

r = c.get("/api/skill-tree")
tree = r.json()
print("tree nodes:", len(tree["nodes"]), "statuses:", sorted({n["status"] for n in tree["nodes"]}))
assert any(n["status"] == "completed" for n in tree["nodes"])

r = c.post("/api/mentor", json={"message": "What should I do today?", "history": []})
assert r.status_code == 200, r.text
m = r.json()
print("mentor source:", m["source"], "| reply:", m["reply"][:90])
assert m["reply"]

r = c.get("/api/state")
assert r.status_code == 200
s = r.json()
assert s["roadmap"] and s["mentor_history"]

r = c.post("/api/mentor", json={"message": "   "})
assert r.status_code == 422

print("ALL TESTS PASSED")

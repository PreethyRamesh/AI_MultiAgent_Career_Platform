"""Integration check: Person 3 (8001) against Person 2 (8000).

Requires both servers:
  cd backend && python -m uvicorn app.main:app --port 8000
  DEMO_MODE=false STATE_API_BASE_URL=http://127.0.0.1:8000 \
      uvicorn main:app --port 8001   (run from person3-dashboard/)
"""
import sys

import httpx

P2 = "http://127.0.0.1:8000"
P3 = "http://127.0.0.1:8001"


def main() -> None:
    state = httpx.get(f"{P2}/api/state", timeout=20).json()
    if not state.get("roadmap"):
        httpx.post(
            f"{P2}/api/roadmap",
            json={
                "target_role": "Data Analyst",
                "current_skills": ["Excel"],
                "skill_gaps": ["Python", "SQL"],
                "hours_per_week": 7,
            },
            timeout=180,
        ).raise_for_status()
        state = httpx.get(f"{P2}/api/state", timeout=20).json()
    print("P2 state ok | role:", state["progress"]["target_role"])

    s = httpx.get(f"{P3}/api/progress/summary", timeout=30).json()
    st = s["state"]
    print("P3 role:", st["role"])
    print("P3 progress:", st["progress"])
    print("P3 missions:", len(st["missions"]),
          "| completed:", sum(1 for m in st["missions"] if m["completed"]))
    print("P3 roadmap items:", len(st["roadmap"]))
    print("P3 skills:", [x["name"] for x in st["skill_tree"]])
    assert st["role"] != "Learner", "role not mapped from Person 2"
    assert st["missions"], "missions not mapped from Person 2"
    assert st["progress"]["xp"] >= 0 and "completion_pct" in st["progress"]
    assert st["skill_tree"], "skill tree not mapped from Person 2"
    assert s["next_mission"] is None or "title" in s["next_mission"]

    snap = httpx.post(f"{P3}/api/progress/snapshot", timeout=30).json()
    print("P3 snapshot:", snap["snapshot"], "| new:", snap["new_achievements"])

    ach = httpx.get(f"{P3}/api/achievements", timeout=30).json()
    earned = [a["key"] for a in ach["achievements"] if a["earned"]]
    print("P3 achievements earned:", earned)

    print("INTEGRATION TEST PASSED")


if __name__ == "__main__":
    sys.exit(main())

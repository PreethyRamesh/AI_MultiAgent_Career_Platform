import httpx

P2 = "http://127.0.0.1:8000"
P3 = "http://127.0.0.1:8001"

day = httpx.get(f"{P2}/api/missions/today", timeout=20).json()
item = next(i for i in day["items"] if not i["done"])
httpx.post(f"{P2}/api/missions/complete", json={"item_id": item["id"]}, timeout=20).raise_for_status()

s = httpx.get(f"{P3}/api/progress/summary", timeout=30).json()
st = s["state"]
print("P3 after P2 mission -> xp:", st["progress"]["xp"],
      "| completed missions:", sum(1 for m in st["missions"] if m["completed"]),
      "| next:", s["next_mission"]["title"] if s["next_mission"] else None)
assert st["progress"]["xp"] > 0

snap = httpx.post(f"{P3}/api/progress/snapshot", timeout=30).json()
print("new achievements:", snap["new_achievements"])
assert "first_mission" in snap["new_achievements"], snap

skills = st["skill_tree"]
print("skill coverage sample:", skills[:3])
print("MISSION FLOW TEST PASSED")

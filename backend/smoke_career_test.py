"""Hermetic smoke test for the AI Career Analysis module (Person 1).

Run:  python smoke_career_test.py   (from backend/)
No API key required — exercises the deterministic engine end-to-end.
"""

from fastapi.testclient import TestClient

from app import config
from app.main import app

config.GEMINI_API_KEY = ""  # hermetic: force deterministic fallbacks

c = TestClient(app)

# --- page ---------------------------------------------------------------
r = c.get("/career")
assert r.status_code == 200, r.text
assert "AI Career Analysis" in r.text

# --- 1. profile & goal setup --------------------------------------------
profile = {
    "name": "Preethy",
    "degree": "B.E. Computer Science",
    "year_of_study": "3rd year",
    "current_skills": ["Python", "SQL", "HTML", "CSS"],
    "target_job_role": "Data Analyst",
    "career_goal": "Become a data analyst in a product company",
}
r = c.post("/api/career/profile", json=profile)
assert r.status_code == 200, r.text
assert r.json()["profile"]["target_job_role"] == "Data Analyst"

# --- 2. resume analysis --------------------------------------------------
resume = """
PREE THY
B.E. Computer Science, 3rd year, CGPA 8.9

SKILLS
Python, SQL, HTML, CSS, Excel, Machine Learning basics, Git

PROJECTS
1. Student Performance Predictor - built a regression model with Python and pandas
   to predict exam scores from attendance data.
2. Library Management System - MySQL database design, CRUD app, REST APIs.

CERTIFICATIONS
- Coursera: Python for Everybody
- NPTEL: Data Base Management System

INTERNSHIP
Data analyst intern at XYZ - dashboards with Power BI
"""
r = c.post("/api/career/resume", json={"content": resume})
assert r.status_code == 200, r.text
res = r.json()
print("resume skills:", [s["name"] for s in res["matched_skills"]])
assert res["education"] and res["certifications"]
assert any("Python" == s["name"] for s in res["matched_skills"])

# --- 3. project analysis ------------------------------------------------
projects = {
    "projects": [
        {"title": "Movie Recommendation Engine", "description": "Python, pandas, scikit-learn collaborative filtering on a MovieLens dataset"},
        {"title": "Weather Dashboard", "description": "Flask web app, REST API, Chart.js, deployed on AWS"},
    ]
}
r = c.post("/api/career/projects", json=projects)
assert r.status_code == 200, r.text
pj = r.json()
print("project skills:", pj["all_skills"])
assert pj["projects"][0]["skills"], "expected project skills"

# --- 4. coursework analysis ----------------------------------------------
courses = {
    "courses": [
        {"name": "Data Structures and Algorithms", "description": ""},
        {"name": "DBMS", "description": ""},
        {"name": "Machine Learning", "description": ""},
        {"name": "Communication Skills", "description": ""},
    ]
}
r = c.post("/api/career/coursework", json=courses)
assert r.status_code == 200, r.text
cw = r.json()
print("coursework skills:", cw["all_skills"])
assert "SQL" in cw["all_skills"]

# --- 6. target job analysis ----------------------------------------------
jd = {
    "title": "Data Analyst",
    "description": """We are hiring a fresher Data Analyst. Responsibilities: analyze
    datasets with SQL and Excel, build Power BI dashboards, present insights.
    Strong analytical thinking and communication. Bachelor's degree required.""",
}
r = c.post("/api/career/job", json=jd)
assert r.status_code == 200, r.text
job = r.json()
print("job tech:", job["technologies"], "| quals:", job["qualifications"])
assert "SQL" in job["technologies"] and "Power BI" in job["technologies"]

# --- full analysis (5,7,8,9,10) ------------------------------------------
r = c.post("/api/career/analyze", json={})
assert r.status_code == 200, r.text
a = r.json()
assert a["profile"] and a["assessment"] and a["gaps"] and a["match"] and a["mapping"]
print("score:", a["match"]["score"], a["match"]["grade"])
print("has:", [h["skill"] for h in a["gaps"]["has"]])
print("improving:", [i["skill"] for i in a["gaps"]["improving"]])
print("missing:", [m["skill"] for m in a["gaps"]["missing"]])
print("top rec:", a["recommendations"][0]["role"], a["recommendations"][0]["match_pct"])
assert 0 <= a["match"]["score"] <= 100
assert a["recommendations"], "expected recommendations"
assert a["mapping"]["mappings"], "expected skill->job mapping"

# --- integration with Person 2's roadmap ---------------------------------
r = c.post("/api/career/skill-gaps")
assert r.status_code == 200, r.text
g = r.json()
print("skill-gaps -> target:", g["target_role"], "gaps:", g["skill_gaps"][:5])
assert g["target_role"] == "Data Analyst"
assert g["skill_gaps"], "expected skill gaps to publish to /api/roadmap"

# Person 2's /api/roadmap should accept the payload shape we publish.
r = c.post("/api/roadmap", json={**g, "hours_per_week": 7})
assert r.status_code == 200, r.text
assert r.json()["progress"]["roadmap_ready"]

# --- reset ---------------------------------------------------------------
r = c.post("/api/career/reset")
assert r.status_code == 200 and r.json()["analysis"] is None

# --- validation -----------------------------------------------------------
r = c.post("/api/career/resume", json={"content": ""})
assert r.status_code == 422
r = c.post("/api/career/skill-gaps")
assert r.status_code in (404, 422)  # nothing to analyze after reset

print("ALL CAREER TESTS PASSED")
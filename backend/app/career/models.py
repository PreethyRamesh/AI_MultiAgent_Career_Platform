"""Pydantic models for the AI Career Analysis module (Person 1)."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


class StudentProfile(BaseModel):
    name: str = ""
    degree: str = ""
    year_of_study: str = ""
    current_skills: list[str] = []
    target_job_role: str = ""
    career_goal: str = ""


class ResumeIn(BaseModel):
    content: str = Field(min_length=1)


class ProjectItem(BaseModel):
    title: str = ""
    description: str = ""


class ProjectsIn(BaseModel):
    projects: list[ProjectItem] = []


class CourseItem(BaseModel):
    name: str = ""
    description: str = ""


class CourseworkIn(BaseModel):
    courses: list[CourseItem] = []


class JobIn(BaseModel):
    title: str = ""
    description: str = Field(min_length=1)


class FullAnalysisIn(BaseModel):
    profile: Optional[StudentProfile] = None
    resume: Optional[ResumeIn] = None
    projects: Optional[ProjectsIn] = None
    coursework: Optional[CourseworkIn] = None
    job: Optional[JobIn] = None


# ---------------------------------------------------------------------------
# Skill evidence & assessment
# ---------------------------------------------------------------------------


class SkillEvidence(BaseModel):
    skill: str
    category: str = "Other"
    level: int = 0
    status: Literal["has", "improving"] = "improving"
    sources: list[dict] = []


class CategoryBreakdown(BaseModel):
    category: str
    skill_count: int = 0
    level_total: int = 0
    avg_level: float = 0.0
    pct: float = 0.0
    skills: list[str] = []


class SkillAssessment(BaseModel):
    skills: list[SkillEvidence] = []
    categories: list[CategoryBreakdown] = []
    strengths: list[SkillEvidence] = []
    summary: dict = {}


# ---------------------------------------------------------------------------
# Resume / projects / coursework / job analysis
# ---------------------------------------------------------------------------


class ResumeOut(BaseModel):
    education: list[str] = []
    projects: list[str] = []
    experience: list[str] = []
    certifications: list[str] = []
    matched_skills: list[dict] = []
    ai_source: Literal["gemini", "fallback"] = "fallback"


class ProjectAnalysis(BaseModel):
    title: str = ""
    description: str = ""
    skills: list[str] = []
    skills_detail: list[dict] = []
    summary: str = ""


class ProjectAnalysisOut(BaseModel):
    projects: list[ProjectAnalysis] = []
    all_skills: list[str] = []


class CourseAnalysis(BaseModel):
    name: str = ""
    skills: list[str] = []


class CourseworkOut(BaseModel):
    courses: list[CourseAnalysis] = []
    all_skills: list[str] = []


class JobAnalysis(BaseModel):
    title_hint: str = ""
    required_skills: list[dict] = []
    soft_skills: list[dict] = []
    qualifications: list[str] = []
    technologies: list[str] = []
    ai_source: Literal["gemini", "fallback"] = "fallback"


# ---------------------------------------------------------------------------
# Gap / match / recommendations / mapping
# ---------------------------------------------------------------------------


class GapItem(BaseModel):
    skill: str
    category: str = "Other"
    level: int = 0
    in_job_note: str = ""


class GapReport(BaseModel):
    has: list[GapItem] = []
    improving: list[GapItem] = []
    missing: list[GapItem] = []
    extra_skills: list[str] = []


class MatchFactor(BaseModel):
    name: str
    weight: float = 0.0
    value: float = 0.0
    impact: Literal["positive", "negative", "neutral"] = "neutral"


class MatchResult(BaseModel):
    score: int = 0
    grade: str = "Not assessed"
    factors: list[MatchFactor] = []
    matched_skills: list[str] = []
    missing_skills: list[str] = []


class Recommendation(BaseModel):
    role: str
    summary: str = ""
    match_pct: int = 0
    matched: list[str] = []
    missing: list[str] = []
    goal_match: bool = False


class SkillMapping(BaseModel):
    requirement: str
    category: str = "Other"
    status: Literal["has", "improving", "missing"] = "missing"
    satisfied_by: list[dict] = []
    note: str = ""


class SkillToJobMapping(BaseModel):
    mappings: list[SkillMapping] = []
    covered: int = 0
    missing: int = 0
    missing_requirements: list[str] = []


class CareerAnalysis(BaseModel):
    profile: Optional[StudentProfile] = None
    assessment: Optional[SkillAssessment] = None
    job: Optional[JobAnalysis] = None
    gaps: Optional[GapReport] = None
    match: Optional[MatchResult] = None
    recommendations: list[Recommendation] = []
    mapping: Optional[SkillToJobMapping] = None


class SkillGapsOut(BaseModel):
    target_role: str = ""
    current_skills: list[str] = []
    skill_gaps: list[str] = []
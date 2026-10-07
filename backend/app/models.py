from typing import Literal, Optional

from pydantic import BaseModel, Field


class Resource(BaseModel):
    title: str
    url: str = ""


class Milestone(BaseModel):
    id: str
    title: str
    details: str = ""
    skills: list[str] = []
    resources: list[Resource] = []
    xp: int = 50
    type: Literal["learn", "practice", "build", "review"] = "learn"


class Phase(BaseModel):
    id: str
    title: str
    goal: str = ""
    duration: str = ""
    milestones: list[Milestone] = []


class Roadmap(BaseModel):
    target_role: str
    hours_per_week: int = 7
    current_skills: list[str] = []
    phases: list[Phase] = []


class ProfileIn(BaseModel):
    target_role: str
    current_skills: list[str] = []
    skill_gaps: list[str] = []
    hours_per_week: int = Field(default=7, ge=1, le=80)


class MissionItem(BaseModel):
    id: str
    milestone_id: str
    phase_id: str
    title: str
    type: Literal["learn", "practice", "build", "review"] = "learn"
    xp: int = 50
    done: bool = False


class MissionDay(BaseModel):
    date: str
    items: list[MissionItem] = []


class CompleteIn(BaseModel):
    item_id: str


class ChatIn(BaseModel):
    message: str
    history: list[dict] = []


class MentorReply(BaseModel):
    reply: str
    source: Literal["gemini", "fallback"] = "fallback"


class ProgressOut(BaseModel):
    xp: int = 0
    level: int = 1
    streak: int = 0
    completed_milestones: list[str] = []
    total_milestones: int = 0
    completion_pct: float = 0.0
    roadmap_ready: bool = False
    target_role: str = ""


class SkillNode(BaseModel):
    id: str
    title: str
    phase_id: str
    skills: list[str] = []
    prereq: Optional[str] = None
    status: Literal["locked", "available", "completed"] = "locked"


class SkillTreeOut(BaseModel):
    role: str
    phases: list[dict] = []
    nodes: list[SkillNode] = []

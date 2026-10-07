from typing import Any

from ..models import Roadmap, SkillNode, SkillTreeOut


def build(state: dict[str, Any]) -> SkillTreeOut:
    roadmap_data = state.get("roadmap")
    if not roadmap_data:
        return SkillTreeOut(role="", phases=[], nodes=[])
    roadmap = Roadmap(**roadmap_data)
    completed = set(state.get("completed", []))
    nodes: list[SkillNode] = []
    phases_meta: list[dict] = []
    prev_id: str | None = None
    for phase in roadmap.phases:
        phases_meta.append({"id": phase.id, "title": phase.title})
        for ms in phase.milestones:
            if ms.id in completed:
                status = "completed"
            elif prev_id is None or prev_id in completed:
                status = "available"
            else:
                status = "locked"
            nodes.append(
                SkillNode(
                    id=ms.id,
                    title=ms.title,
                    phase_id=phase.id,
                    skills=ms.skills,
                    prereq=prev_id,
                    status=status,
                )
            )
            prev_id = ms.id
    return SkillTreeOut(role=roadmap.target_role, phases=phases_meta, nodes=nodes)

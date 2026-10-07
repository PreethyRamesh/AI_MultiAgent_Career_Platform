"""AI Career Analysis module (Person 1).

Serverside package for profile/goal setup, resume/project/coursework
analysis, AI skill assessment, target job analysis, skill-gap analysis,
job match score, career recommendations and skill-to-job mapping.

Integration (for teammates):
    from .career import router as career_router
    app.include_router(career_router)

See backend/career/README.md for the full API contract.
"""

from .router import router

__all__ = ["router"]
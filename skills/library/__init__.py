"""
Skills library — ~99 skills across 16 domains.
Each module registers its skills into the SkillRegistry on import.
"""
from skills.library import (
    discovery,
    architecture,
    frontend,
    backend,
    data,
    mobile,
    devops,
    security,
    quality,
    documentation,
    integration,
    realtime,
    workflow,
    nextjs,
    flutter,
    blazor,
)

__all__ = [
    "discovery", "architecture", "frontend", "backend",
    "data", "mobile", "devops", "security",
    "quality", "documentation", "integration", "realtime",
    "workflow", "nextjs", "flutter", "blazor",
]

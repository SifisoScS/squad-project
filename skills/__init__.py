"""
Skills layer — import this package to load the full skills library.

~99 skills across 16 domains: discovery, architecture, frontend, backend,
data, mobile, devops, security, quality, documentation, integration, realtime,
workflow, nextjs, flutter, blazor.

Usage anywhere:
    from skills import SkillRegistry
    result = SkillRegistry.invoke("system_design", prompt, workspace=path)

Or via any agent:
    output = self.invoke_skill("threat_model", description)
"""
import skills.library  # registers all skills as a side effect
from skills.registry import Skill, SkillRegistry, SkillAgent

__all__ = ["Skill", "SkillRegistry", "SkillAgent"]

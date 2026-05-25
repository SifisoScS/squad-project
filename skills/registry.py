"""
Skills layer — reusable, named Claude capabilities that any agent can invoke.

Inspired by Claude Code's slash-command skill system: each skill is a focused
expert invocation with its own system prompt, tool access, and response contract.
Skills are composable building blocks — agents use them without caring how they work.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Skill:
    """
    A named, reusable Claude capability.

    name        — unique identifier used to look up and invoke the skill
    description — one-liner surfaced in skill listings and tool-choice prompts
    category    — discovery | engineering | quality | documentation
    system_prompt — the expert-level system prompt for this skill
    tools       — tool names (from tools.registry TOOL_DEFINITIONS) this skill may call
    """
    name: str
    description: str
    category: str
    system_prompt: str
    tools: list[str] = field(default_factory=list)


class SkillAgent:
    """
    Lightweight, single-use agent that executes one skill invocation.
    Uses BaseAgent's full machinery (prompt caching, tool loop) without
    a persistent identity — lives only for the duration of one skill call.

    self._skill is assigned before BaseAgent.__init__() so that
    _create_system_prompt() can read it when the parent constructor fires.
    """

    # Deferred to avoid circular imports at module load
    _BaseAgent = None

    @classmethod
    def _get_base(cls):
        if cls._BaseAgent is None:
            from agents.base import BaseAgent
            cls._BaseAgent = BaseAgent
        return cls._BaseAgent

    def __init__(self, skill: Skill, workspace: Path | None = None):
        self._skill = skill

        Base = self._get_base()

        # Build a throwaway BaseAgent subclass whose system prompt is the skill prompt.
        # self._skill is captured via the enclosing scope — no class-level mutation needed.
        outer_skill = skill

        class _Agent(Base):  # type: ignore[valid-type]
            def _create_system_prompt(self) -> str:
                return outer_skill.system_prompt

        self._agent = _Agent(
            name=f"[skill:{skill.name}]",
            roles=[],
            workspace=workspace,
        )

    def invoke(self, task: str) -> str:
        """Run the skill on `task`. Returns the skill's text response."""
        from tools.registry import TOOL_DEFINITIONS

        self._agent.messages = []  # fresh context per invocation

        if not self._skill.tools:
            return self._agent.think(task)

        tools = [
            TOOL_DEFINITIONS[n]
            for n in self._skill.tools
            if n in TOOL_DEFINITIONS
        ]
        return self._agent.act(task, tools)


class SkillRegistry:
    """
    Global catalogue of registered skills.
    Skills are registered at import time by skills/catalog.py and are
    available to any agent via BaseAgent.invoke_skill().
    """

    _skills: dict[str, Skill] = {}

    @classmethod
    def register(cls, skill: Skill) -> None:
        cls._skills[skill.name] = skill

    @classmethod
    def get(cls, name: str) -> Skill:
        if name not in cls._skills:
            available = ", ".join(sorted(cls._skills))
            raise KeyError(f"Skill '{name}' not found. Available: {available}")
        return cls._skills[name]

    @classmethod
    def invoke(
        cls,
        name: str,
        task: str,
        workspace: Path | None = None,
    ) -> str:
        """Invoke skill `name` on `task`. Returns the skill's text output."""
        skill = cls.get(name)
        agent = SkillAgent(skill, workspace=workspace)
        return agent.invoke(task)

    @classmethod
    def list_skills(cls, category: str | None = None) -> list[Skill]:
        skills = list(cls._skills.values())
        if category:
            skills = [s for s in skills if s.category == category]
        return sorted(skills, key=lambda s: (s.category, s.name))

    @classmethod
    def describe(cls) -> str:
        """Human-readable catalogue — useful for agent context injection."""
        lines = ["## Available Skills\n"]
        current_cat = ""
        for skill in cls.list_skills():
            if skill.category != current_cat:
                current_cat = skill.category
                lines.append(f"\n### {current_cat.capitalize()}\n")
            lines.append(f"- `{skill.name}` — {skill.description}")
        return "\n".join(lines)

    @classmethod
    def chain(
        cls,
        skill_names: list[str],
        task: str,
        workspace: Path | None = None,
    ) -> dict[str, str]:
        """
        Skill composition pipeline (#9).

        Runs each skill in sequence. The output of skill N is appended as
        additional context when invoking skill N+1, so later skills benefit
        from prior reasoning without sharing conversation state.

        Returns an ordered dict of {skill_name: output} for every step.

        Example:
            results = SkillRegistry.chain(
                ["decompose", "system_design", "adr"],
                "Design a real-time notification service",
            )
            adr_text = results["adr"]
        """
        if not skill_names:
            raise ValueError("chain() requires at least one skill name")

        results: dict[str, str] = {}
        context = task

        for name in skill_names:
            output = cls.invoke(name, context, workspace=workspace)
            results[name] = output
            # Pipe this skill's output into the next skill's context
            context = (
                f"Original task: {task}\n\n"
                f"--- Output from '{name}' skill ---\n{output}"
            )

        return results

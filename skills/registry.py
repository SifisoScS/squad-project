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

    name          — unique identifier used to look up and invoke the skill
    description   — one-liner surfaced in skill listings and tool-choice prompts
    category      — discovery | engineering | quality | documentation
    system_prompt — the expert-level system prompt for this skill
    tools         — tool names (from tools.registry TOOL_DEFINITIONS) this skill may call
    depends_on    — (5.1) other skill names that must run before this one in compose()
    output_schema — (5.2) optional JSON Schema dict; if set, output is validated after invocation
    """
    name: str
    description: str
    category: str
    system_prompt: str
    tools: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    output_schema: dict | None = None


class SkillAgent:
    """
    Lightweight, single-use agent that executes one skill invocation.
    Uses BaseAgent's full machinery (prompt caching, tool loop) without
    a persistent identity — lives only for the duration of one skill call.
    """

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

        self._agent.messages = []

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
        """Invoke skill `name` on `task`. Validates output schema if defined (5.2)."""
        skill = cls.get(name)
        agent = SkillAgent(skill, workspace=workspace)
        output = agent.invoke(task)

        # 5.2: Optional output schema validation
        if skill.output_schema:
            try:
                import json
                parsed = json.loads(output)
                # Simple presence check — full jsonschema validation requires the
                # jsonschema package which is optional; fall through on ImportError.
                try:
                    import jsonschema
                    jsonschema.validate(parsed, skill.output_schema)
                except ImportError:
                    pass  # jsonschema not installed; skip deep validation
                except jsonschema.ValidationError as e:
                    return json.dumps({
                        "validation_failed": True,
                        "skill": name,
                        "error": str(e.message),
                        "raw_output": output[:500],
                    })
            except (json.JSONDecodeError, TypeError):
                pass  # output is not JSON — skip schema validation

        return output

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
        Skill composition pipeline.

        Runs each skill in sequence. The output of skill N is appended as
        additional context when invoking skill N+1, so later skills benefit
        from prior reasoning without sharing conversation state.

        Returns an ordered dict of {skill_name: output} for every step.
        """
        if not skill_names:
            raise ValueError("chain() requires at least one skill name")

        results: dict[str, str] = {}
        context = task

        for name in skill_names:
            output = cls.invoke(name, context, workspace=workspace)
            results[name] = output
            context = (
                f"Original task: {task}\n\n"
                f"--- Output from '{name}' skill ---\n{output}"
            )

        return results

    @classmethod
    def _topological_sort(cls, skill_names: list[str]) -> list[str]:
        """
        Topological sort of skill_names respecting their depends_on declarations (5.1).
        Raises ValueError on cycles.
        """
        # Build subgraph restricted to requested skills
        graph: dict[str, list[str]] = {}
        for name in skill_names:
            try:
                skill = cls.get(name)
                deps = [d for d in skill.depends_on if d in skill_names]
            except KeyError:
                deps = []
            graph[name] = deps

        # Kahn's algorithm
        in_degree: dict[str, int] = {n: 0 for n in graph}
        for deps in graph.values():
            for d in deps:
                in_degree[d] = in_degree.get(d, 0) + 1

        queue = [n for n in graph if in_degree[n] == 0]
        order: list[str] = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for dependent, deps in graph.items():
                if node in deps:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        if len(order) != len(skill_names):
            raise ValueError(f"Skill dependency cycle detected among: {skill_names}")
        return order

    @classmethod
    def compose(
        cls,
        skill_names: list[str],
        task: str,
        workspace: Path | None = None,
    ) -> dict[str, str]:
        """
        Skill composition with dependency graph resolution (5.1).

        Like chain() but respects each skill's depends_on field — topologically
        sorts the skill names before running the pipeline.

        Example:
            results = SkillRegistry.compose(
                ["adr", "system_design", "decompose"],
                "Design a payment service",
            )
            # Runs: decompose → system_design → adr (dependency order)
        """
        ordered = cls._topological_sort(skill_names)
        return cls.chain(ordered, task, workspace=workspace)

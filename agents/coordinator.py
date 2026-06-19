from pathlib import Path
from agents.base import BaseAgent, _AGILE_TEAM_CONTEXT
from tools.registry import get_tools_for_role


class Coordinator(BaseAgent):
    """
    Tech Lead / Coordinator — quality gate between implementation and completion.
    Reviews every task before it is marked done. Can spawn parameterized specialists
    for tasks that need deep expertise outside a generalist developer's wheelhouse.
    """

    def _create_system_prompt(self) -> str:
        roles_text = "\n".join(f"- {r}" for r in self.roles)
        return f"""You are {self.name}, the Coordinator and Tech Lead of an autonomous software factory.

## Your Role

You have final say over every piece of work before it moves forward. You maintain
architectural consistency across the codebase, catch quality and security issues early,
and ensure the project delivers exactly what was designed. You are rigorous without
being pedantic — approve good-enough work, reject work that would cause real problems.

## Your Responsibilities

{roles_text}

## How You Review Work

When reviewing an implemented task:
1. Read ARCHITECTURE.md to understand the design intent and tech stack
2. Use list_files to see what was actually created or modified
3. Read the implementation files most relevant to the task
4. Evaluate against: architecture alignment, security, code quality, completeness
5. Give a clear, specific verdict

Your verdict MUST begin with exactly one of these structured lines as the very first line of your response:
  VERDICT: APPROVED
  VERDICT: REJECTED

After the verdict line, provide your reasoning. When rejecting: name the file, the exact issue, and what the correct fix is.
Vague feedback wastes everyone's time. Be surgical.

## Quality Bar

**Approve if:** task requirements are met, no obvious security holes (SQL injection, hardcoded
secrets, missing auth checks), code is readable and testable, structure matches ARCHITECTURE.md.

**Reject if:** core functionality is missing, security vulnerabilities present, code crashes
on import, direct contradiction of ARCHITECTURE.md, incomplete stubs passed off as implementation.

Do NOT reject for style preferences alone. Do NOT approve broken code to move fast.

## Specialist Decisions

When asked whether a task needs a specialist, be honest and specific:
- Respond "NO" if a competent generalist developer can handle it well
- Respond with a one-line specialist description if deep expertise is genuinely needed
  (e.g. "PostgreSQL migration specialist with SQLAlchemy expertise")

{_AGILE_TEAM_CONTEXT}

## Response Style

Direct, specific, decisive. No hedging. When approving, one sentence is enough.
When rejecting, bullet each issue with file + line context where possible.
"""

    # Keywords that signal a task warrants a targeted security_audit skill pass
    _SECURITY_KEYWORDS = frozenset([
        "auth", "jwt", "token", "password", "secret", "credential", "login",
        "register", "session", "cookie", "encrypt", "hash", "sql", "query",
        "database", "migration", "permission", "role", "admin", "user",
    ])

    def _is_security_sensitive(self, task) -> bool:
        text = (task.title + " " + task.description).lower()
        return any(kw in text for kw in self._SECURITY_KEYWORDS)

    def review_task(self, task, workspace: Path) -> dict:
        """
        Review an implemented task against architecture and quality bar.
        For security-sensitive tasks, automatically runs the `security_audit`
        skill first and folds its findings into the review context.
        Returns {"approved": bool, "feedback": str, "skill_audit": str | None}.
        """
        skill_audit: str | None = None

        if self._is_security_sensitive(task):
            try:
                skill_audit = self.invoke_skill(
                    "security_audit",
                    f"Perform a security audit of the files most relevant to this task.\n\n"
                    f"Task: {task.title}\n"
                    f"Description: {task.description}\n\n"
                    f"Read the implementation files related to this task and audit them "
                    f"against the OWASP Top 10 and common application security vulnerabilities.",
                )
            except Exception as e:
                skill_audit = f"[security_audit skill failed: {e}]"

        self.messages = []
        tools = get_tools_for_role("coordinator")

        audit_context = (
            f"\n\nSecurity Audit Skill Output (run automatically for this security-sensitive task):\n"
            f"{skill_audit}\n\n"
            f"Factor these findings into your APPROVED / REJECTED verdict."
            if skill_audit else ""
        )

        result = self.act(
            f"Review this completed implementation task.\n\n"
            f"Task: {task.title}\n"
            f"Description: {task.description}\n"
            f"{audit_context}\n"
            f"Steps:\n"
            f"1. Read ARCHITECTURE.md\n"
            f"2. Call list_files('.') to see what exists in the workspace\n"
            f"3. Read the implementation files most relevant to this task\n"
            f"4. Evaluate: architecture alignment, security, code quality, completeness\n"
            f"5. Start your response with 'VERDICT: APPROVED' or 'VERDICT: REJECTED' on the first line, "
            f"followed by your specific reasoning.",
            tools,
        )
        # 1.6: Parse only the first line to avoid false positives from quoted text
        first_line = result.strip().splitlines()[0].upper() if result.strip() else ""
        approved = first_line.startswith("VERDICT: APPROVED")
        return {"approved": approved, "feedback": result, "skill_audit": skill_audit}

    def needs_specialist(self, task) -> tuple[bool, str]:
        """
        Ask Claude whether this task warrants a specialist beyond a generalist developer.
        Returns (needs_specialist: bool, role_description: str).
        """
        result = self.think(
            f"Does this task require a specialist beyond a general-purpose developer?\n\n"
            f"Task: {task.title}\n"
            f"Description: {task.description}\n\n"
            f"Consider whether deep expertise is genuinely needed in: database design and migrations, "
            f"cryptography or auth protocols, frontend/CSS/accessibility, DevOps/infrastructure, "
            f"performance optimization, or ML/data pipelines.\n\n"
            f"If a generalist developer can handle this well, respond with exactly: NO\n"
            f"If a specialist is genuinely needed, respond with a single descriptive line "
            f"(e.g. 'Database migration specialist with PostgreSQL and Alembic expertise')."
        )
        if result.strip().upper().startswith("NO"):
            return False, ""
        return True, result.strip()

    def suggest_approach(self, task) -> dict:
        """
        Recommend the best approach for a task from three options:
          - generalist developer (no assistance needed)
          - a skill from the SkillRegistry (targeted capability)
          - a specialist agent (full specialist Developer spawn)

        Returns {"mode": "generalist"|"skill"|"specialist",
                 "skill_name": str | None,
                 "specialist_role": str | None}.
        """
        from skills import SkillRegistry
        skill_catalogue = SkillRegistry.describe()

        result = self.think(
            f"Decide the best approach for implementing this task.\n\n"
            f"Task: {task.title}\n"
            f"Description: {task.description}\n\n"
            f"## Available Skills\n{skill_catalogue}\n\n"
            f"Options:\n"
            f"1. GENERALIST — a senior developer can implement this without special assistance\n"
            f"2. SKILL:<skill_name> — run one of the available skills above before or during implementation\n"
            f"   (e.g. 'SKILL:decompose' to break the task down, 'SKILL:db_migration' for schema changes)\n"
            f"3. SPECIALIST:<description> — spawn a specialist agent with deep domain expertise\n"
            f"   (e.g. 'SPECIALIST:PostgreSQL migration expert with Alembic')\n\n"
            f"Respond with exactly one of these formats on the first line:\n"
            f"GENERALIST\n"
            f"SKILL:<skill_name>\n"
            f"SPECIALIST:<one-line description>\n\n"
            f"Followed by one sentence of rationale."
        )
        first_line = result.strip().splitlines()[0].strip().upper()

        if first_line.startswith("SKILL:"):
            skill_name = first_line[len("SKILL:"):].strip().lower()
            return {"mode": "skill", "skill_name": skill_name, "specialist_role": None}
        if first_line.startswith("SPECIALIST:"):
            role = result.strip().splitlines()[0][len("SPECIALIST:"):].strip()
            return {"mode": "specialist", "skill_name": None, "specialist_role": role}
        return {"mode": "generalist", "skill_name": None, "specialist_role": None}

    def spawn_specialist(self, role_description: str) -> "Developer":
        """
        Instantiate a Developer with a specialized system prompt derived from role_description.
        No subclass required — just a parameterized BaseAgent.
        """
        from agents.developer import Developer

        return Developer(
            name=f"Specialist ({role_description[:40]})",
            roles=[
                f"You are a specialist in: {role_description}",
                "Read ARCHITECTURE.md before implementing any task to understand the full system",
                "Write production-quality code within your specialty area",
                "Use tools to create and verify files in the project workspace",
                "Do not introduce patterns or dependencies that conflict with the existing architecture",
            ],
        )

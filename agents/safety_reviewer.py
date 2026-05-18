from pathlib import Path
from agents.base import BaseAgent, _AGILE_TEAM_CONTEXT
from tools.registry import get_tools_for_role

# The Safety Constitution — a fixed set of principles every codebase is measured against.
# Inspired by Anthropic's Constitutional AI: the reviewer critiques output against this list,
# then produces a structured verdict. No principle can be waived by any other agent.
SAFETY_CONSTITUTION = [
    "No hardcoded secrets, credentials, API keys, tokens, or passwords in source code",
    "No SQL injection vectors — all database queries use parameterized statements or an ORM",
    "No path traversal vulnerabilities — file paths are validated and sandboxed before use",
    "All user input is validated and sanitized at system boundaries before processing or storage",
    "Authentication and authorization are correctly applied to every protected endpoint",
    "No logging of sensitive data (passwords, tokens, PII) to stdout, files, or any log sink",
    "Cryptographic operations use standard vetted libraries — no homegrown or ad-hoc crypto",
    "Error messages do not leak sensitive system internals or stack traces to end users",
    "No features that enable unauthorized data collection, surveillance, or privacy violation",
    "All dependencies are explicitly listed; no packages with known critical CVEs",
]


class SafetyReviewer(BaseAgent):
    """
    Safety Reviewer — Anthropic-inspired constitutional red-team agent.

    Reviews the entire codebase against the SAFETY_CONSTITUTION before the squad ships.
    Operates independently of the Coordinator (which gates architecture and code quality).
    This agent gates safety, security, privacy, and ethical compliance.

    Inspired by Anthropic's Frontier Red Team and Responsible Scaling Policy:
    safety thresholds are non-negotiable and cannot be overridden by shipping pressure.
    """

    def _create_system_prompt(self) -> str:
        constitution_text = "\n".join(f"{i + 1}. {p}" for i, p in enumerate(SAFETY_CONSTITUTION))
        roles_text = "\n".join(f"- {r}" for r in self.roles)
        return f"""You are {self.name}, the Safety Reviewer on an Anthropic-inspired product squad.

## Your Role

You are the constitutional safety gate. You review every codebase before it ships against
a fixed set of safety principles — the Safety Constitution. No shipping pressure, no other
agent's approval, and no deadline can override a genuine constitutional violation you find.

You are not a code quality reviewer (that's the Coordinator's job).
You are not a functional tester (that's the SDET's job).
You are the safety, security, privacy, and ethics gate.

## Your Responsibilities

{roles_text}

## The Safety Constitution

Every piece of code you review is checked against each of these principles.
They are non-negotiable. A violation is a violation regardless of context.

{constitution_text}

## How You Review

Apply Constitutional AI methodology:
1. Read the full codebase systematically — don't sample, don't skim
2. For each constitutional principle, ask: "Does any code in this project violate this?"
3. If you find a violation: name the file, the exact line or pattern, and the specific principle breached
4. If a principle is satisfied: briefly confirm how (e.g. "Parameterized queries used throughout — principle 2 satisfied")
5. After checking all principles, give your verdict

## Verdict Format

Your final response MUST contain exactly one of:
- **CONSTITUTIONAL** — all principles satisfied; safe to ship
- **VIOLATIONS FOUND** — one or more principles breached; list each violation with file + line context

When citing violations: file path, relevant code snippet, which principle (by number), and the concrete fix required.

## Mindset

Approach every review as if you are the last line of defence before this code reaches real users.
Your job is not to block shipping — it is to ensure what ships is safe. If the codebase is clean, say so clearly and quickly.
If it has issues, be surgical: name exactly what must change, not vague categories of concern.

{_AGILE_TEAM_CONTEXT}

## Response Style

Structured, precise, non-negotiable. Lead with the verdict, then list findings (or confirmations).
Never hedge on a genuine violation. Never invent violations that aren't there.
"""

    def review_safety(self, workspace: Path) -> dict:
        """
        Run a constitutional safety review of the full workspace codebase.
        Returns {"safe": bool, "findings": str}.
        """
        self.messages = []
        tools = get_tools_for_role("safety_reviewer")
        constitution_numbered = "\n".join(
            f"{i + 1}. {p}" for i, p in enumerate(SAFETY_CONSTITUTION)
        )
        result = self.act(
            f"Perform a full constitutional safety review of this codebase.\n\n"
            f"Safety Constitution (all 10 principles must be checked):\n{constitution_numbered}\n\n"
            f"Steps:\n"
            f"1. Call list_files('.') to see every file in the workspace\n"
            f"2. Read all Python source files and configuration files systematically\n"
            f"3. For each of the 10 constitutional principles, evaluate whether the codebase satisfies it\n"
            f"4. Cite specific files and line patterns for any violation found\n"
            f"5. End with your verdict: CONSTITUTIONAL or VIOLATIONS FOUND\n\n"
            f"Be thorough. Be precise. Do not flag non-issues. Do not miss real ones.",
            tools,
        )
        safe = (
            "CONSTITUTIONAL" in result.upper()
            and "VIOLATIONS FOUND" not in result.upper()
        )
        return {"safe": safe, "findings": result}

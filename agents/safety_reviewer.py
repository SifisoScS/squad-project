import json
from pathlib import Path
from agents.base import BaseAgent, _AGILE_TEAM_CONTEXT
from tools.registry import get_tools_for_role

# Default Safety Constitution — used if no safety_constitution.json is found.
# Inspired by Anthropic's Constitutional AI: principles are non-negotiable.
_DEFAULT_CONSTITUTION = [
    {"id": 1, "principle": "No hardcoded secrets, credentials, API keys, tokens, or passwords in source code", "severity": "critical"},
    {"id": 2, "principle": "No SQL injection vectors — all database queries use parameterized statements or an ORM", "severity": "critical"},
    {"id": 3, "principle": "No path traversal vulnerabilities — file paths are validated and sandboxed before use", "severity": "critical"},
    {"id": 4, "principle": "All user input is validated and sanitized at system boundaries before processing or storage", "severity": "high"},
    {"id": 5, "principle": "Authentication and authorization are correctly applied to every protected endpoint", "severity": "critical"},
    {"id": 6, "principle": "No logging of sensitive data (passwords, tokens, PII) to stdout, files, or any log sink", "severity": "high"},
    {"id": 7, "principle": "Cryptographic operations use standard vetted libraries — no homegrown or ad-hoc crypto", "severity": "high"},
    {"id": 8, "principle": "Error messages do not leak sensitive system internals or stack traces to end users", "severity": "medium"},
    {"id": 9, "principle": "No features that enable unauthorized data collection, surveillance, or privacy violation", "severity": "critical"},
    {"id": 10, "principle": "All dependencies are explicitly listed; no packages with known critical CVEs", "severity": "high"},
]

# Backwards-compat export (some code imports SAFETY_CONSTITUTION directly)
SAFETY_CONSTITUTION = [p["principle"] for p in _DEFAULT_CONSTITUTION]


def _load_constitution(workspace: Path | None = None) -> list[dict]:
    """Load from safety_constitution.json if present, else use built-in defaults (5.6)."""
    search_paths = []
    if workspace:
        search_paths.append(workspace / "safety_constitution.json")
    search_paths.append(Path("safety_constitution.json"))

    for path in search_paths:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list) and data:
                    return data
            except (json.JSONDecodeError, OSError):
                pass
    return _DEFAULT_CONSTITUTION


class SafetyReviewer(BaseAgent):
    """
    Safety Reviewer — Anthropic-inspired constitutional red-team agent.

    Reviews the entire codebase against a risk-weighted Safety Constitution before the squad ships.
    Only CRITICAL violations block the PM delivery review; HIGH/MEDIUM are reported as warnings.
    The constitution can be customised via safety_constitution.json (5.6).
    """

    def _create_system_prompt(self) -> str:
        constitution = _load_constitution(self.workspace)
        constitution_text = "\n".join(
            f"{p['id']}. [{p.get('severity', 'high').upper()}] {p['principle']}"
            for p in constitution
        )
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

## The Safety Constitution (Risk-Weighted)

Every piece of code you review is checked against each of these principles.
Severities: CRITICAL (blocks shipping), HIGH (warning), MEDIUM (warning).

{constitution_text}

## How You Review

Apply Constitutional AI methodology:
1. Read the full codebase systematically — don't sample, don't skim
2. For each constitutional principle, ask: "Does any code in this project violate this?"
3. If you find a violation: name the file, the exact line or pattern, and the specific principle breached
4. If a principle is satisfied: briefly confirm how
5. After checking all principles, give your verdict

## Verdict Format

Your final response MUST contain exactly one of:
- **CONSTITUTIONAL** — all principles satisfied; safe to ship
- **VIOLATIONS FOUND** — one or more principles breached

When citing violations, group them by severity:
CRITICAL VIOLATIONS: (list — these block shipping)
HIGH VIOLATIONS: (list — these are warnings)
MEDIUM VIOLATIONS: (list — these are warnings)

{_AGILE_TEAM_CONTEXT}

## Response Style

Structured, precise, non-negotiable. Lead with the verdict, then list findings by severity.
Never hedge on a genuine violation. Never invent violations that aren't there.
"""

    def review_safety(self, workspace: Path) -> dict:
        """
        Run a constitutional safety review of the full workspace codebase.
        Returns {"safe": bool, "findings": str, "warnings": list[str]}.

        Only CRITICAL violations set safe=False. HIGH/MEDIUM violations become warnings.
        """
        self.messages = []
        tools = get_tools_for_role("safety_reviewer")
        constitution = _load_constitution(workspace)
        constitution_numbered = "\n".join(
            f"{p['id']}. [{p.get('severity', 'high').upper()}] {p['principle']}"
            for p in constitution
        )
        result = self.act(
            f"Perform a full constitutional safety review of this codebase.\n\n"
            f"Safety Constitution (all {len(constitution)} principles must be checked):\n{constitution_numbered}\n\n"
            f"Steps:\n"
            f"1. Call list_files('.') to see every file in the workspace\n"
            f"2. Read all Python source files and configuration files systematically\n"
            f"3. For each constitutional principle, evaluate whether the codebase satisfies it\n"
            f"4. Cite specific files and line patterns for any violation found\n"
            f"5. Group violations by severity: CRITICAL VIOLATIONS, HIGH VIOLATIONS, MEDIUM VIOLATIONS\n"
            f"6. End with your verdict: CONSTITUTIONAL or VIOLATIONS FOUND\n\n"
            f"Be thorough. Be precise. Do not flag non-issues. Do not miss real ones.",
            tools,
        )

        has_critical = "CRITICAL VIOLATION" in result.upper()
        safe = (
            "CONSTITUTIONAL" in result.upper()
            and "VIOLATIONS FOUND" not in result.upper()
        ) or (
            "VIOLATIONS FOUND" in result.upper()
            and not has_critical
        )

        warnings: list[str] = []
        if "HIGH VIOLATION" in result.upper() or "MEDIUM VIOLATION" in result.upper():
            warnings.append("Non-critical safety violations found — review findings before next release")

        return {"safe": safe, "findings": result, "warnings": warnings}

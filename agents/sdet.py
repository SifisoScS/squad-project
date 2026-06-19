import re
from pathlib import Path
from agents.base import BaseAgent, _AGILE_TEAM_CONTEXT
from tools.registry import get_tools_for_role


class SDET(BaseAgent):
    """
    AI-powered Software Development Engineer in Test.
    """

    def _create_system_prompt(self) -> str:
        roles_text = "\n".join(f"- {r}" for r in self.roles)
        return f"""You are {self.name}, a Software Development Engineer in Test (SDET) on an agile team.

## Your Role

You are a quality-focused engineer who bridges development and testing. You design and implement
automated test suites, analyze failures, report defects with precision, and work with developers
to make code more testable. You think adversarially — your job is to find what breaks before
production does. You treat test code with the same quality standards as production code.

Your testing stack: pytest, Playwright (E2E), requests (API testing), coverage.py, CI/CD integration.
You write tests that are deterministic, fast, and maintainable. You avoid flaky tests at all costs.

## Your Responsibilities in This Sprint

{roles_text}

## How You Approach Your Work

When designing tests:
- Start from the acceptance criteria — every criterion must have at least one test
- Identify the test pyramid layers: unit (fast, isolated), integration (real dependencies), E2E (critical paths)
- Think about edge cases, boundary conditions, and failure scenarios — not just the happy path
- Prioritize tests by risk: what failure would hurt users most?

When analyzing test results:
- Distinguish failures from flakes — a failing test that sometimes passes is hiding a real bug
- Root-cause failures before reporting — shallow defect reports waste developer time
- Track trends: is coverage increasing? Are the same areas failing repeatedly?

When reporting defects:
- Follow the format: summary, severity, environment, steps to reproduce, expected vs actual, evidence
- Severity: Critical (data loss / security), High (blocking feature), Medium (degraded experience), Low (cosmetic)
- Include the minimal reproduction case — the shorter, the better

When collaborating with developers:
- Review code for testability during design, not after implementation
- Suggest dependency injection, interface extraction, or seam points where needed
- Treat developer pushback on tests as a signal to improve the test, not lower the bar

{_AGILE_TEAM_CONTEXT}

## Response Style

Respond as {self.name} — methodical, detail-oriented, and quality-focused. Be precise about
what you tested, what passed, what failed, and what the evidence shows. When reporting defects,
always include severity and reproduction steps. Never say "it should work" — only what you observed.
"""

    def design_tests(self, feature: str) -> str:
        return self.think(
            f"Design a test plan for this feature:\n\n{feature}\n\n"
            "Cover all test pyramid layers: unit tests (what isolated logic to verify), "
            "integration tests (what component interactions to validate), and E2E tests "
            "(what critical user flows to exercise). Include edge cases, boundary conditions, "
            "and failure scenarios. Name specific test cases with their expected outcomes."
        )

    def analyze_results(self, test_summary: str) -> str:
        return self.think(
            f"Analyze these test results:\n\n{test_summary}\n\n"
            "Identify: which tests failed and their likely root causes, any flaky tests, "
            "coverage gaps, and your recommended actions for the team. "
            "Distinguish between code bugs, test bugs, and environment issues."
        )

    def report_defect(self, defect_info: str) -> str:
        return self.think(
            f"Write a formal defect report based on this information:\n\n{defect_info}\n\n"
            "Format: Summary (one line), Severity (Critical/High/Medium/Low with justification), "
            "Environment, Steps to Reproduce (numbered), Expected Result, Actual Result, "
            "and any additional evidence or notes."
        )

    def test_task(self, task, workspace: Path) -> dict:
        """Write and run tests for a completed implementation task."""
        self.messages = []
        tools = get_tools_for_role("sdet")
        result_text = self.act(
            f"Write and run tests for this completed task.\n\n"
            f"Task: {task.title}\n"
            f"Description: {task.description}\n\n"
            f"Steps:\n"
            f"1. Read ARCHITECTURE.md to understand the system\n"
            f"2. Read the implementation files relevant to this task\n"
            f"3. Write comprehensive pytest tests to tests/test_{_snake(task.title)}.py "
            f"   covering happy paths, edge cases, and error conditions\n"
            f"4. Run the tests with run_tests and report pass/fail counts\n"
            f"5. Run run_bandit on the implementation directory for security issues\n"
            f"6. Run run_ruff on the implementation directory for code quality violations\n\n"
            f"In your final response include: "
            f"test results (X passed, Y failed), "
            f"security issues found by bandit (or 'skipped' if not installed), "
            f"linting violations found by ruff (or 'skipped' if not installed).",
            tools,
        )
        return _parse_test_results(result_text)


def _snake(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


def _parse_test_results(text: str) -> dict:
    passed = int(m.group(1)) if (m := re.search(r"(\d+)\s+passed", text)) else 0
    failed = int(m.group(1)) if (m := re.search(r"(\d+)\s+failed", text)) else 0

    # 2.7: Detect skipped security/lint checks and flag them
    security_check_skipped = (
        "skipped" in text.lower() and
        ("bandit" in text.lower() or "security" in text.lower())
    )
    lint_check_skipped = (
        "skipped" in text.lower() and
        ("ruff" in text.lower() or "lint" in text.lower())
    )

    result: dict = {"passed": passed, "failed": failed, "output": text}
    if security_check_skipped:
        result["security_check_skipped"] = True
    if lint_check_skipped:
        result["lint_check_skipped"] = True
    return result

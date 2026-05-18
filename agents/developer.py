from pathlib import Path
from agents.base import BaseAgent, _AGILE_TEAM_CONTEXT
from tools.registry import get_tools_for_role


class Developer(BaseAgent):
    """
    AI-powered software developer. Uses Claude to write code, review pull requests,
    debug issues, and collaborate with the SDET on test coverage.
    """

    def _create_system_prompt(self) -> str:
        roles_text = "\n".join(f"- {r}" for r in self.roles)
        return f"""You are {self.name}, a Senior Software Developer on an agile team.

## Your Role

You are an experienced software developer who writes clean, well-structured, testable code.
You care deeply about code quality, maintainability, and performance. You mentor junior developers,
participate actively in code reviews, and collaborate closely with the SDET to ensure your code
is easy to test. You approach problems with systematic thinking — breaking down complex tasks into
clear steps and making deliberate technical decisions with documented rationale.

Your technical stack: Python, REST APIs, SQL databases, Git, CI/CD pipelines, Docker.
You apply SOLID principles, write meaningful commit messages, and keep pull requests small and focused.

## Your Responsibilities in This Sprint

{roles_text}

## How You Approach Your Work

When writing code:
- Start by clarifying acceptance criteria and edge cases before writing a single line
- Choose the simplest solution that meets requirements — avoid premature abstraction
- Write tests alongside the code, not after
- Leave the codebase cleaner than you found it

When reviewing code:
- Focus on correctness, security, performance, and maintainability — in that order
- Be specific: reference the exact concern, explain why it matters, suggest an alternative
- Distinguish between blocking issues and optional improvements

When debugging:
- Reproduce the issue first, form a hypothesis, then validate — never guess and apply random fixes
- Check logs, add tracing, isolate the failing component

When collaborating with the SDET:
- Share your design intent so they can write meaningful tests
- Treat test failures as useful signals, not inconveniences
- Proactively flag code that is hard to test and refactor it

{_AGILE_TEAM_CONTEXT}

## Response Style

Respond as {self.name} — a pragmatic, technically sharp developer. Be specific and concrete.
When describing code work, name the specific functions, modules, or APIs involved. When asked for
an opinion, give one with reasoning. Never be vague about technical decisions.
"""

    def write_code(self, task: str) -> str:
        return self.think(
            f"You have been assigned this development task:\n\n{task}\n\n"
            "Describe the implementation approach you will take, the key technical decisions, "
            "the code structure you plan to create, and any risks or open questions. "
            "Be specific about function names, modules, and data models."
        )

    def review_code(self, code_description: str) -> str:
        return self.think(
            f"You are reviewing this code or pull request:\n\n{code_description}\n\n"
            "Provide a thorough code review. For each issue found: state the specific problem, "
            "explain why it matters (correctness, security, performance, maintainability), "
            "and suggest a concrete alternative. Separate blocking issues from suggestions."
        )

    def debug(self, issue: str) -> str:
        return self.think(
            f"You are investigating this bug:\n\n{issue}\n\n"
            "Walk through your debugging process: how you reproduced it, your hypothesis "
            "about the root cause, what you checked to validate that hypothesis, "
            "and the fix you are implementing."
        )

    def implement_task(self, task, workspace: Path) -> str:
        """Implement a backlog task by actually writing code files to disk."""
        self.messages = []  # fresh context per task to prevent bloat
        tools = get_tools_for_role("developer")
        return self.act(
            f"Implement this task for the project.\n\n"
            f"Task: {task.title}\n"
            f"Description: {task.description}\n\n"
            f"Start by reading ARCHITECTURE.md to understand the system design and tech stack. "
            f"Then read any existing files relevant to this task. "
            f"Write production-quality implementation code. "
            f"You may call run_python to do a quick syntax/import check on your files. "
            f"When done, summarize which files you created or modified and what each does.",
            tools,
        )

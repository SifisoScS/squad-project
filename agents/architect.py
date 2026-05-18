from agents.base import BaseAgent, _AGILE_TEAM_CONTEXT
from tools.registry import get_tools_for_role


class Architect(BaseAgent):
    """
    AI-powered Software Architect. Uses Claude with file tools to design any project:
    writes ARCHITECTURE.md, creates the directory structure, and produces
    backlog_tasks.json that the TeamLead loads into the sprint backlog.
    """

    def _create_system_prompt(self) -> str:
        roles_text = "\n".join(f"- {r}" for r in self.roles)
        return f"""You are {self.name}, a Senior Software Architect on an autonomous software development team.

## Your Role

You are the first agent to act on any new project. Your job is to turn a project description
into a concrete system design and a scaffolded workspace that the development team can build from.
You think in terms of components, interfaces, and data flow — not implementation details.
You make deliberate technology choices and document the rationale.

You have access to file tools. You MUST use them — describing architecture in text alone is not enough.
Your deliverables are files on disk, not just ideas.

## Your Responsibilities

{roles_text}

## What You Must Produce for Every Project

1. **Directory structure** — call `create_directory` for every top-level directory the project needs
   (e.g. `src`, `tests`, `docs`). Create subdirectories as needed.

2. **ARCHITECTURE.md** — write this to the workspace root. Include:
   - Project overview (1 paragraph)
   - Tech stack with rationale for each choice
   - Component breakdown (what each module/service does)
   - Data models (key entities and their fields)
   - API contracts (endpoints, request/response shapes if applicable)
   - Directory structure (explain what goes where)
   - Development setup instructions

3. **backlog_tasks.json** — write this to the workspace root. A JSON array of tasks in
   dependency order (foundational tasks first, features after, integration/tests last).
   Each task: {{"title": "...", "description": "..."}}
   Include 6-10 tasks. Descriptions must be specific enough for a developer to implement
   without asking follow-up questions.

## How You Approach Design

- Start with the simplest architecture that meets the requirements
- Choose boring, proven technology over novel alternatives
- Design for testability from the start (dependency injection, clear interfaces)
- Make the directory structure communicate the architecture
- Order backlog tasks by dependency: you cannot implement features before you have models

{_AGILE_TEAM_CONTEXT}

## Tool Usage

Always follow this sequence:
1. Call `create_directory` for each directory you need
2. Call `write_file` for ARCHITECTURE.md
3. Call `write_file` for backlog_tasks.json
4. Summarize what you designed in your final text response

Never just describe what you will do — use the tools to actually do it.
"""

    def design_project(self, spec) -> str:
        tools = get_tools_for_role("architect")
        tech_stack = spec.tech_stack_str()
        prompt = f"""Design the complete system for this project and write all architecture artifacts to disk.

Project name: {spec.name}
Tech stack: {tech_stack}

Project description:
{spec.description}

Your mandatory deliverables (use your tools):
1. Create all required directories with create_directory
2. Write ARCHITECTURE.md to the workspace root
3. Write backlog_tasks.json to the workspace root

backlog_tasks.json must be a valid JSON array:
[
  {{"title": "Task title", "description": "Detailed description covering what to implement, which files to create, and acceptance criteria"}},
  ...
]

Order tasks from foundational (models, DB setup, config) to features to integration.
Include 6-10 tasks. Make descriptions specific and actionable.
"""
        return self.act(prompt, tools)

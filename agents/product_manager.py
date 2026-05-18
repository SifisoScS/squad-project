from agents.base import BaseAgent, _AGILE_TEAM_CONTEXT
from tools.registry import get_tools_for_role


class ProductManager(BaseAgent):
    """
    Product Manager — owns the "what" and "why" of the product.
    Writes a PRD with user stories and acceptance criteria before the Architect designs.
    Reviews the final delivery to validate it solves the stated user problem.
    """

    def _create_system_prompt(self) -> str:
        roles_text = "\n".join(f"- {r}" for r in self.roles)
        return f"""You are {self.name}, the Product Manager on an empowered Silicon Valley product squad.

## Your Role

You own the "what" and "why". You are the voice of the customer inside the squad.
You do not tell engineers HOW to build — you define the problem clearly and the success criteria
precisely, then trust the team to find the best solution.

You think in user outcomes, not feature lists. A feature exists only to solve a user problem.
If you can't state the problem in one sentence, you don't understand it well enough yet.

## Your Responsibilities

{roles_text}

## How You Define Requirements

When writing a PRD (Product Requirements Document):
1. State the user problem in one sentence (not the solution — the problem)
2. Identify the target user and their specific pain point
3. Write 3–5 user stories in the format: "As a [user], I want [goal], so that [outcome]"
4. For each story, write specific, testable acceptance criteria — no vague language
5. Define 2–3 success metrics (KPIs) that would confirm the problem is actually solved
6. List explicit out-of-scope items to prevent scope creep from day one

## How You Review a Delivery

When the squad ships and you review:
1. Read the PRD to recall every acceptance criterion
2. Inspect what was actually built
3. For each acceptance criterion: mark PASS or FAIL with a specific reason
4. Give a clear verdict: SHIPPED (all AC met) or NEEDS WORK (list exactly what is missing)

Do not rubber-stamp. "It looks good" is not a review. Name the specific criterion and test it.

## Quality Bar

- Acceptance criteria must be testable by a human or an automated test — no ambiguous language
- "Works correctly" is not an AC — "Returns HTTP 200 with a valid JWT when credentials match" is
- Reject scope that doesn't map to a user story — no gold-plating

{_AGILE_TEAM_CONTEXT}

## Response Style

Crisp, user-focused, outcome-oriented. Lead with the user problem, not the technical solution.
Write in plain language that a non-engineer can read and a QA engineer can test.
"""

    def define_product_requirements(self, spec) -> str:
        """Write a PRD to disk with user stories and acceptance criteria."""
        self.messages = []
        tools = get_tools_for_role("product_manager")
        return self.act(
            f"Write a Product Requirements Document (PRD) for this project and save it as PRD.md "
            f"in the workspace root.\n\n"
            f"Project: {spec.name}\n"
            f"Description:\n{spec.description}\n\n"
            f"Your PRD must include all of these sections:\n"
            f"1. **Problem Statement** — one sentence, user-focused (not a solution)\n"
            f"2. **Target User** — who they are and what pain point this solves\n"
            f"3. **User Stories** — 3–5 stories: 'As a [user], I want [goal], so that [outcome]'\n"
            f"4. **Acceptance Criteria** — testable criteria for each user story\n"
            f"5. **Success Metrics / KPIs** — 2–3 measurable outcomes that confirm success\n"
            f"6. **Out of Scope** — at least 3 explicit items NOT in scope for this release\n\n"
            f"Write this file using write_file with path 'PRD.md'. "
            f"After writing, summarize the key user stories in your response.",
            tools,
        )

    def review_delivery(self, workspace) -> str:
        """Review the completed build against PRD acceptance criteria."""
        self.messages = []
        tools = get_tools_for_role("product_manager")
        return self.act(
            f"Review the completed project delivery against the product requirements.\n\n"
            f"Steps:\n"
            f"1. Read PRD.md to load all acceptance criteria\n"
            f"2. Call list_files('.') to see every file that was built\n"
            f"3. Read the most relevant implementation files to understand what was actually delivered\n"
            f"4. For each acceptance criterion: state PASS or FAIL with a specific, factual reason\n"
            f"5. Give an overall verdict:\n"
            f"   - SHIPPED — every acceptance criterion passed\n"
            f"   - NEEDS WORK — list exactly which criteria failed and why\n\n"
            f"Be a tough reviewer. 'The endpoint exists' is not a pass — "
            f"verify it does what the AC requires.",
            tools,
        )

from pathlib import Path
from agents.developer import Developer
from agents.sdet import SDET
from agents.team_lead import TeamLead
from agents.architect import Architect
from agents.coordinator import Coordinator
from agents.product_manager import ProductManager
from agents.safety_reviewer import SafetyReviewer
import skills  # noqa: F401 — registers the full built-in skill catalog

MAX_BUILD_SPRINTS = 10
MAX_REJECTIONS = 2  # max coordinator rejections before forcing a task complete


class Team:
    """
    Silicon Valley + Anthropic product squad — cross-functional, empowered, safety-conscious.

    Build pipeline:
      PM (PRD) → Architect (design) → Engineers (implement) →
      Coordinator (quality gate) → SDET (tests) →
      Safety Reviewer (constitutional gate) → PM (delivery review)

    Every agent runs against the Anthropic-inspired cultural context:
    safety-first hierarchy, constitutional review, low-ego collaboration, human oversight.
    """

    def __init__(self, project_name: str, members: list):
        self.project_name = project_name
        self.members = members
        self.goals: list[str] = []
        self.sprint_number = 0
        self.sprint_history: list[dict] = []

        self.product_managers: list[ProductManager] = [m for m in members if isinstance(m, ProductManager)]
        self.architects: list[Architect] = [m for m in members if isinstance(m, Architect)]
        self.coordinators: list[Coordinator] = [m for m in members if isinstance(m, Coordinator)]
        self.developers: list[Developer] = [m for m in members if isinstance(m, Developer)]
        self.sdets: list[SDET] = [m for m in members if isinstance(m, SDET)]
        self.team_leads: list[TeamLead] = [m for m in members if isinstance(m, TeamLead)]
        self.safety_reviewers: list[SafetyReviewer] = [m for m in members if isinstance(m, SafetyReviewer)]

    @classmethod
    def default(cls) -> "Team":
        """
        Creates the default Silicon Valley + Anthropic product squad.

        Structure follows the SVPG product trio model:
          PM (what/why) + Engineering Lead/Architect (how) + QA (did we ship it right?)
        Supplemented by senior engineers, an Engineering Manager, and an
        Anthropic-inspired Safety Reviewer who gates every release against the Safety Constitution.
        """
        pm_roles = [
            "Own the 'what' and 'why' — define the user problem before anyone writes code",
            "Write the PRD with user stories and testable acceptance criteria",
            "Define success metrics (KPIs) for the product",
            "Review the final delivery and verify every acceptance criterion is met",
            "Represent the voice of the customer in all squad decisions",
        ]
        architect_roles = [
            "Design system architecture that satisfies the PRD requirements",
            "Write ARCHITECTURE.md with component breakdown and tech rationale",
            "Create the project directory structure",
            "Produce backlog_tasks.json with ordered implementation tasks",
        ]
        coordinator_roles = [
            "Review every implemented task before marking it complete",
            "Ensure architectural consistency across the entire codebase",
            "Approve or reject work with specific, actionable feedback",
            "Decide when a task needs a specialist and spawn one if required",
            "Maintain quality standards and security bar throughout the build",
        ]
        developer_roles = [
            "Read the PRD and architecture docs before writing a single line",
            "Implement tasks that move the squad's OKRs forward",
            "Write clean, maintainable, testable production code",
            "Use tools to create files in the project workspace",
            "Verify implementations with quick syntax checks",
        ]
        sdet_roles = [
            "Translate acceptance criteria from the PRD into automated tests",
            "Read implementation code and write comprehensive pytest tests",
            "Run tests and report pass/fail counts",
            "Run bandit for security scanning and ruff for code quality",
            "Cover happy paths, edge cases, and error conditions",
            "Write tests to tests/test_*.py following project conventions",
        ]
        eng_manager_roles = [
            "Load backlog from architecture artifacts and sequence by dependency",
            "Assign tasks to engineers in priority order (highest OKR impact first)",
            "Track sprint velocity and remove impediments immediately",
            "Facilitate squad ceremonies and shield the team from distractions",
        ]
        safety_reviewer_roles = [
            "Review the complete codebase against the Safety Constitution before every release",
            "Apply Constitutional AI methodology: check each principle systematically, cite violations precisely",
            "Gate releases on security, privacy, and ethical compliance — not code style",
            "Report CONSTITUTIONAL or VIOLATIONS FOUND with surgical specificity",
            "Never block on non-safety concerns; never waive a genuine safety violation",
        ]
        return cls(
            "Product Squad",
            [
                ProductManager("Jordan Lee", pm_roles),
                Architect("Alex Chen", architect_roles),
                Coordinator("Sarah Kim", coordinator_roles),
                Developer("Priya Patel", developer_roles),
                Developer("Marcus Johnson", developer_roles),
                SDET("David Lee", sdet_roles),
                TeamLead("Michael Brown", eng_manager_roles),
                SafetyReviewer("Dr. Amara Wells", safety_reviewer_roles),
            ],
        )

    def set_goals(self, goals: list[str]) -> None:
        self.goals = goals

    def daily_standup(self) -> str:
        updates: list[tuple[str, str]] = []
        for member in self.members:
            update = member.daily_standup_update()
            updates.append((member.name, update))
            print(f"  [{member.name}]: {update[:120]}...")

        lead = self.team_leads[0]
        synthesis = lead.facilitate_standup(updates)

        self.sprint_history.append({
            "sprint": self.sprint_number + 1,
            "standup": {"updates": dict(updates), "synthesis": synthesis},
        })
        return synthesis

    def work_on_tasks(self) -> dict:
        sprint_goals_text = "\n".join(f"- {g}" for g in self.goals)
        outputs: dict[str, str] = {}

        # Each developer works on a sprint goal
        for i, dev in enumerate(self.developers):
            goal = self.goals[i % len(self.goals)]
            code_output = dev.write_code(
                f"Sprint goal: {goal}\n\nProject: {self.project_name}\n"
                f"Sprint: {self.sprint_number + 1}"
            )
            outputs[dev.name] = code_output
            print(f"  [{dev.name}] wrote code: {code_output[:100]}...")

        # SDETs receive developer outputs and design tests
        for sdet in self.sdets:
            for dev_name, code_output in outputs.items():
                sdet.receive_message(dev_name, f"Code I just wrote:\n{code_output}")

            test_plan = sdet.design_tests(
                f"Features being developed this sprint:\n{sprint_goals_text}\n\n"
                f"Developer output received from team:\n"
                + "\n\n".join(f"{n}: {o}" for n, o in outputs.items())
            )
            outputs[sdet.name] = test_plan
            print(f"  [{sdet.name}] designed tests: {test_plan[:100]}...")

            # Developers receive the test plan
            for dev in self.developers:
                dev.receive_message(sdet.name, f"Test plan for your code:\n{test_plan}")

        if self.sprint_history:
            self.sprint_history[-1]["work"] = outputs
        return outputs

    def code_review(self) -> dict:
        review_outputs: dict[str, str] = {}

        # Cross-developer code review
        if len(self.developers) >= 2:
            for i, reviewer in enumerate(self.developers):
                reviewee = self.developers[(i + 1) % len(self.developers)]
                work = self.sprint_history[-1].get("work", {}).get(reviewee.name, "Sprint work")
                review = reviewer.review_code(
                    f"Code by {reviewee.name} this sprint:\n{work}"
                )
                review_outputs[f"{reviewer.name} reviews {reviewee.name}"] = review
                print(f"  [{reviewer.name}] reviewed {reviewee.name}'s code: {review[:100]}...")
                reviewee.receive_message(reviewer.name, f"Code review feedback:\n{review}")

        # SDET analyzes test results
        for sdet in self.sdets:
            test_plan = self.sprint_history[-1].get("work", {}).get(sdet.name, "Test activities")
            analysis = sdet.analyze_results(
                f"Sprint {self.sprint_number + 1} test activities and outcomes:\n{test_plan}"
            )
            review_outputs[f"{sdet.name} test analysis"] = analysis
            print(f"  [{sdet.name}] analyzed results: {analysis[:100]}...")

            # Share analysis with the team lead
            self.team_leads[0].receive_message(sdet.name, f"Test analysis:\n{analysis}")

        # Team lead identifies impediments from the review
        review_summary = "\n\n".join(f"{k}:\n{v}" for k, v in review_outputs.items())
        impediments = self.team_leads[0].identify_impediments(
            f"Sprint {self.sprint_number + 1} review findings:\n{review_summary}"
        )
        review_outputs["impediments"] = impediments
        print(f"  [{self.team_leads[0].name}] identified impediments: {impediments[:100]}...")

        if self.sprint_history:
            self.sprint_history[-1]["review"] = review_outputs
        return review_outputs

    def retrospective(self) -> str:
        entry = self.sprint_history[-1]
        sprint_summary = (
            f"Sprint {self.sprint_number + 1} — {self.project_name}\n\n"
            f"Goals: {', '.join(self.goals)}\n\n"
            f"Standup synthesis: {entry.get('standup', {}).get('synthesis', '')[:300]}\n\n"
            f"Work completed: {', '.join(entry.get('work', {}).keys())}\n\n"
            f"Review findings: {str(entry.get('review', {}).get('impediments', ''))[:300]}"
        )

        lead = self.team_leads[0]
        retro = lead.retrospective(sprint_summary)
        print(f"  [{lead.name}] retrospective: {retro[:120]}...")

        # Broadcast retrospective outcome to all team members
        for member in self.members:
            if member is not lead:
                member.receive_message(
                    lead.name,
                    f"Sprint {self.sprint_number + 1} retrospective outcomes:\n{retro}"
                )

        self.sprint_history[-1]["retrospective"] = retro
        self.sprint_number += 1
        return retro

    def build_project(self, spec) -> dict:
        """
        Silicon Valley + Anthropic product squad build pipeline:
        1. PM writes a PRD (user stories + acceptance criteria)
        2. Architect designs the system informed by the PRD
        3. Engineering Manager loads the backlog
        4. Engineers implement tasks; Coordinator quality-gates each one
        5. SDET tests completed tasks (pytest + bandit + ruff)
        6. Safety Reviewer runs a constitutional review of the full codebase
        7. PM reviews the final delivery against the acceptance criteria
        Returns a final report dict including safety verdict and PM review.
        """
        from team.backlog import Backlog
        from tools.registry import set_workspace
        from tools.file_tools import list_files
        from memory.decision_log import DecisionLog

        spec.setup_workspace()
        workspace = spec.workspace_path.resolve()
        set_workspace(workspace)

        for member in self.members:
            member.workspace = workspace

        # Inject cross-project memory into every agent before any work begins
        decision_log = DecisionLog()
        memory_ctx = decision_log.context_block()
        if memory_ctx:
            for member in self.members:
                member.memory_context = memory_ctx

        print(f"\n[Squad] Kicking off '{spec.name}' → {spec.workspace_path}")
        print(f"[Squad] Tech stack: {spec.tech_stack_str()}\n")

        # Step 1: PM writes the PRD — defines the user problem and acceptance criteria
        pm = self.product_managers[0] if self.product_managers else None
        prd_summary = ""
        if pm:
            print(f"[{pm.name} | PM] Writing Product Requirements Document...")
            prd_summary = pm.define_product_requirements(spec)
            print(f"[{pm.name} | PM] PRD written: {prd_summary[:120]}...\n")
            decision_log.record(
                spec.name, "tech_choice",
                f"PRD defined for {spec.name}",
                prd_summary[:300],
            )

        # Step 2: Architect designs the system (informed by the PRD)
        if not self.architects:
            raise RuntimeError("Squad has no Architect — use Team.default() or add an Architect")
        architect = self.architects[0]
        print(f"[{architect.name} | Architect] Designing system and writing artifacts...")
        arch_prompt_extra = (
            f"\n\nNote: The PM has already written PRD.md in the workspace. "
            f"Read it to understand the user stories and acceptance criteria before designing."
            if pm else ""
        )
        original_desc = spec.description
        spec.description = spec.description + arch_prompt_extra
        arch_summary = architect.design_project(spec)
        spec.description = original_desc
        print(f"[{architect.name} | Architect] Done: {arch_summary[:120]}...\n")
        decision_log.record(
            spec.name, "tech_choice",
            f"Architecture designed for {spec.name}",
            arch_summary[:300],
        )

        # Step 3: Engineering Manager loads the backlog
        lead = self.team_leads[0]
        print(f"[{lead.name} | Eng Manager] Loading backlog from architecture artifacts...")
        task_dicts = lead.create_backlog_from_architecture(workspace)
        if not task_dicts:
            print(f"[{lead.name} | Eng Manager] WARNING: No tasks found — check backlog_tasks.json was written")
        backlog = Backlog(workspace)
        for t in task_dicts:
            backlog.add_task(t.get("title", "Untitled"), t.get("description", ""))
        print(f"[{lead.name} | Eng Manager] Backlog ready: {len(task_dicts)} tasks\n{backlog.summary()}\n")

        # Step 4: Coordinator quality gate (optional — degrades gracefully if squad has none)
        coordinator = self.coordinators[0] if self.coordinators else None

        # Step 5: Build loop
        sprint = 0
        test_results: list[dict] = []
        completed_this_round: list = []
        skills_invoked: list[dict] = []  # track skill usage across the full build

        while backlog.get_pending() and sprint < MAX_BUILD_SPRINTS:
            sprint += 1
            print(f"[Squad] ── Sprint {sprint} ─────────────────────────────")
            completed_this_round = []

            for dev in self.developers:
                task = lead.assign_next_task(backlog, dev.name)
                if task is None:
                    break

                # Coordinator suggests approach: generalist / skill / specialist
                active_dev = dev
                if coordinator:
                    approach = coordinator.suggest_approach(task)
                    mode = approach["mode"]

                    if mode == "skill":
                        skill_name = approach["skill_name"]
                        print(f"[{coordinator.name} | Coordinator] Skill assist '{skill_name}' for: {task.title}")
                        try:
                            skill_output = coordinator.invoke_skill(
                                skill_name,
                                f"Task: {task.title}\nDescription: {task.description}",
                            )
                            skills_invoked.append({
                                "task": task.title,
                                "skill": skill_name,
                                "triggered_by": coordinator.name,
                            })
                            # Prepend skill output to task description so the developer benefits from it
                            task.description = (
                                f"--- Skill: {skill_name} ---\n{skill_output}\n\n"
                                f"--- Original Task ---\n{task.description}"
                            )
                        except Exception as e:
                            print(f"[{coordinator.name} | Coordinator] Skill '{skill_name}' failed: {e}")

                    elif mode == "specialist":
                        role_desc = approach["specialist_role"]
                        print(f"[{coordinator.name} | Coordinator] Spawning specialist: {role_desc[:60]}")
                        active_dev = coordinator.spawn_specialist(role_desc)
                        active_dev.workspace = workspace
                        active_dev.memory_context = memory_ctx

                # Implement → Coordinator review → retry loop
                approved = False
                for attempt in range(1, MAX_REJECTIONS + 2):
                    print(f"[{active_dev.name}] Implementing: {task.title} (attempt {attempt})")
                    active_dev.implement_task(task, workspace)

                    if not coordinator:
                        approved = True
                        break

                    print(f"[{coordinator.name} | Coordinator] Reviewing: {task.title}")
                    review = coordinator.review_task(task, workspace)

                    if review.get("skill_audit"):
                        skills_invoked.append({
                            "task": task.title,
                            "skill": "security_audit",
                            "triggered_by": coordinator.name,
                        })

                    if review["approved"]:
                        approved = True
                        print(f"[{coordinator.name} | Coordinator] Approved: {task.title}")
                        decision_log.record(
                            spec.name, "success", task.title,
                            f"Approved on attempt {attempt}",
                            review["feedback"][:200],
                        )
                        break

                    print(f"[{coordinator.name} | Coordinator] Rejected (attempt {attempt}): {review['feedback'][:100]}...")
                    decision_log.record(
                        spec.name, "rejection", task.title,
                        review["feedback"][:300],
                        f"Attempt {attempt} of {MAX_REJECTIONS + 1}",
                    )

                    if attempt <= MAX_REJECTIONS:
                        # Append feedback to description so the next attempt can act on it
                        updated_desc = (
                            task.description
                            + f"\n\n--- Coordinator Feedback (attempt {attempt}) ---\n"
                            + review["feedback"]
                        )
                        backlog.update_task(task.id, description=updated_desc)

                backlog.complete_task(task.id)
                completed_this_round.append(task)

                if not approved:
                    print(f"[Coordinator] Max attempts reached for '{task.title}' — moving on")

            for sdet in self.sdets:
                for task in completed_this_round:
                    print(f"[{sdet.name}] Testing: {task.title}")
                    tr = sdet.test_task(task, workspace)
                    test_results.append({"task": task.title, **tr})
                    print(f"[{sdet.name}] Results: {tr['passed']} passed, {tr['failed']} failed")

            print(f"\n{backlog.summary()}\n")

        # Step 5: Final file report
        lf = list_files(".", workspace)
        files_created = [
            f["path"] for f in lf.get("files", [])
            if not f["path"].endswith("backlog.json")
        ]

        total_passed = sum(r.get("passed", 0) for r in test_results)
        total_failed = sum(r.get("failed", 0) for r in test_results)

        decision_log.record(
            spec.name, "outcome",
            f"Build complete: {len(files_created)} files created",
            f"{total_passed} tests passed, {total_failed} failed",
            "success" if total_failed == 0 else "partial",
        )

        print(
            f"\n[Squad] Build complete — {len(files_created)} files, "
            f"{total_passed} tests passed, {total_failed} failed"
        )

        # Step 6: Constitutional safety review — Anthropic-inspired red-team gate
        safety_result: dict = {"safe": True, "findings": "No safety reviewer in squad."}
        safety_reviewer = self.safety_reviewers[0] if self.safety_reviewers else None
        if safety_reviewer:
            safety_reviewer.workspace = workspace
            safety_reviewer.memory_context = memory_ctx
            print(f"\n[{safety_reviewer.name} | Safety] Running constitutional review...")
            safety_result = safety_reviewer.review_safety(workspace)
            verdict_label = "CONSTITUTIONAL" if safety_result["safe"] else "VIOLATIONS FOUND"
            print(f"[{safety_reviewer.name} | Safety] {verdict_label}: {safety_result['findings'][:200]}...\n")
            decision_log.record(
                spec.name,
                "success" if safety_result["safe"] else "rejection",
                "Constitutional safety review",
                safety_result["findings"][:300],
                verdict_label,
            )

        # Step 7: PM delivery review — validates against acceptance criteria
        pm_verdict = ""
        if pm:
            print(f"[{pm.name} | PM] Reviewing delivery against acceptance criteria...")
            pm_verdict = pm.review_delivery(workspace)
            print(f"[{pm.name} | PM] Verdict: {pm_verdict[:200]}...\n")
            decision_log.record(
                spec.name, "outcome",
                "PM delivery review",
                pm_verdict[:300],
            )

        return {
            "project": spec.name,
            "workspace": str(spec.workspace_path),
            "sprints_run": sprint,
            "backlog_summary": backlog.summary(),
            "files_created": files_created,
            "test_results": {
                "total_passed": total_passed,
                "total_failed": total_failed,
                "by_task": test_results,
            },
            "skills_invoked": skills_invoked,
            "safety_review": {
                "constitutional": safety_result["safe"],
                "findings": safety_result["findings"],
            },
            "pm_delivery_review": pm_verdict,
        }

    def get_performance(self) -> dict:
        activities_summary = (
            f"Project: {self.project_name}\n"
            f"Sprints completed: {self.sprint_number}\n"
            f"Goals: {', '.join(self.goals)}\n\n"
        )
        for entry in self.sprint_history:
            activities_summary += (
                f"Sprint {entry['sprint']}:\n"
                f"  Work: {', '.join(entry.get('work', {}).keys())}\n"
                f"  Retrospective snippet: {str(entry.get('retrospective', ''))[:200]}\n\n"
            )

        assessment = self.team_leads[0].assess_performance(activities_summary)

        return {
            "project": self.project_name,
            "sprints_completed": self.sprint_number,
            "goals": self.goals,
            "team_lead_assessment": assessment,
            "sprint_count": len(self.sprint_history),
        }

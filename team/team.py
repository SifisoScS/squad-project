import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from agents.developer import Developer
from agents.sdet import SDET
from agents.team_lead import TeamLead
from agents.architect import Architect
from agents.coordinator import Coordinator
from agents.product_manager import ProductManager
from agents.safety_reviewer import SafetyReviewer
import skills  # noqa: F401 — registers the full built-in skill catalog

from config import cfg

MAX_BUILD_SPRINTS = cfg.MAX_BUILD_SPRINTS
MAX_REJECTIONS = cfg.MAX_REJECTIONS


class Team:
    """
    Silicon Valley + Anthropic product squad — cross-functional, empowered, safety-conscious.

    Build pipeline:
      PM (PRD) → Architect (design) → Engineers (implement) →
      Coordinator (quality gate) → SDET (tests) →
      Safety Reviewer (constitutional gate) → PM (delivery review)
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

        self._cancel_requested: bool = False
        self._coordinator_lock = threading.Lock()

    def cancel(self) -> None:
        self._cancel_requested = True

    @classmethod
    def default(cls) -> "Team":
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
            "Produce backlog_tasks.json with ordered implementation tasks and depends_on fields",
        ]
        coordinator_roles = [
            "Review every implemented task before marking it complete",
            "Ensure architectural consistency across the entire codebase",
            "Approve or reject work with VERDICT: APPROVED or VERDICT: REJECTED on the first line",
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
            "Load backlog from architecture artifacts and sequence by dependency order",
            "Assign tasks to engineers in dependency-aware priority order",
            "Track sprint velocity and remove impediments immediately",
            "Facilitate squad ceremonies and shield the team from distractions",
        ]
        safety_reviewer_roles = [
            "Review the complete codebase against the Safety Constitution before every release",
            "Apply Constitutional AI methodology: check each principle systematically, cite violations precisely",
            "Gate releases on CRITICAL violations; report HIGH/MEDIUM violations as warnings",
            "Report CONSTITUTIONAL or VIOLATIONS FOUND with surgical specificity",
            "Never block on non-safety concerns; never waive a genuine critical safety violation",
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

        for i, dev in enumerate(self.developers):
            goal = self.goals[i % len(self.goals)]
            code_output = dev.write_code(
                f"Sprint goal: {goal}\n\nProject: {self.project_name}\n"
                f"Sprint: {self.sprint_number + 1}"
            )
            outputs[dev.name] = code_output
            print(f"  [{dev.name}] wrote code: {code_output[:100]}...")

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

            for dev in self.developers:
                dev.receive_message(sdet.name, f"Test plan for your code:\n{test_plan}")

        if self.sprint_history:
            self.sprint_history[-1]["work"] = outputs
        return outputs

    def code_review(self) -> dict:
        review_outputs: dict[str, str] = {}

        if len(self.developers) >= 2:
            for i, reviewer in enumerate(self.developers):
                reviewee = self.developers[(i + 1) % len(self.developers)]
                work = self.sprint_history[-1].get("work", {}).get(reviewee.name, "Sprint work")
                review = reviewer.review_code(f"Code by {reviewee.name} this sprint:\n{work}")
                review_outputs[f"{reviewer.name} reviews {reviewee.name}"] = review
                print(f"  [{reviewer.name}] reviewed {reviewee.name}'s code: {review[:100]}...")
                reviewee.receive_message(reviewer.name, f"Code review feedback:\n{review}")

        for sdet in self.sdets:
            test_plan = self.sprint_history[-1].get("work", {}).get(sdet.name, "Test activities")
            analysis = sdet.analyze_results(
                f"Sprint {self.sprint_number + 1} test activities and outcomes:\n{test_plan}"
            )
            review_outputs[f"{sdet.name} test analysis"] = analysis
            print(f"  [{sdet.name}] analyzed results: {analysis[:100]}...")
            self.team_leads[0].receive_message(sdet.name, f"Test analysis:\n{analysis}")

        review_summary = "\n\n".join(f"{k}:\n{v}" for k, v in review_outputs.items())
        impediments = self.team_leads[0].identify_impediments(
            f"Sprint {self.sprint_number + 1} review findings:\n{review_summary}"
        )
        review_outputs["impediments"] = impediments

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

        for member in self.members:
            if member is not lead:
                member.receive_message(lead.name, f"Sprint {self.sprint_number + 1} retrospective outcomes:\n{retro}")

        self.sprint_history[-1]["retrospective"] = retro
        self.sprint_number += 1
        return retro

    def build_project(self, spec, checkpoint_callback=None) -> dict:
        """
        Build pipeline:
        1. PM writes PRD
        2. Architect designs system
        3. Engineering Manager loads backlog
        4. Engineers implement tasks (parallel); Coordinator quality-gates each
        5. SDET tests completed tasks
        6. Safety Reviewer constitutional gate
        7. PM delivery review

        checkpoint_callback: optional callable(checkpoint_name) — called at configured
        human_checkpoints to pause the build for human review (5.7).
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

        decision_log = DecisionLog()
        memory_ctx = decision_log.context_block()
        if memory_ctx:
            for member in self.members:
                member.memory_context = memory_ctx

        print(f"\n[Squad] Kicking off '{spec.name}' → {workspace}")
        print(f"[Squad] Tech stack: {spec.tech_stack_str()}\n")

        # 5.5: Build timing and trace
        build_start = time.time()
        agent_traces: list[dict] = []
        timings: dict[str, float] = {}

        def _checkpoint(name: str) -> None:
            if checkpoint_callback and name in getattr(spec, "human_checkpoints", []):
                print(f"[Squad] Checkpoint: {name} — waiting for human approval")
                checkpoint_callback(name)

        # ── Step 1: PM writes PRD ──────────────────────────────────────────────
        pm = self.product_managers[0] if self.product_managers else None
        prd_summary = ""
        if pm:
            t0 = time.time()
            print(f"[{pm.name} | PM] Writing Product Requirements Document...")
            prd_summary = pm.define_product_requirements(spec)
            elapsed = time.time() - t0
            timings["prd"] = elapsed
            agent_traces.append({"agent": pm.name, "step": "define_prd", "duration_s": round(elapsed, 2), "tokens": pm._token_usage.copy()})
            print(f"[{pm.name} | PM] PRD written: {prd_summary[:120]}...\n")
            decision_log.record(spec.name, "tech_choice", f"PRD defined for {spec.name}", prd_summary[:300])
            _checkpoint("after_prd")

        # ── Step 2: Architect designs the system ──────────────────────────────
        if not self.architects:
            raise RuntimeError("Squad has no Architect — use Team.default() or add an Architect")
        architect = self.architects[0]
        t0 = time.time()
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
        elapsed = time.time() - t0
        timings["architecture"] = elapsed
        agent_traces.append({"agent": architect.name, "step": "design_project", "duration_s": round(elapsed, 2), "tokens": architect._token_usage.copy()})
        print(f"[{architect.name} | Architect] Done: {arch_summary[:120]}...\n")
        decision_log.record(spec.name, "tech_choice", f"Architecture designed for {spec.name}", arch_summary[:300])
        _checkpoint("after_architecture")

        # ── Step 3: Engineering Manager loads backlog ─────────────────────────
        lead = self.team_leads[0]
        print(f"[{lead.name} | Eng Manager] Loading backlog from architecture artifacts...")
        task_dicts = lead.create_backlog_from_architecture(workspace)
        if not task_dicts:
            print(f"[{lead.name} | Eng Manager] WARNING: No tasks found — check backlog_tasks.json was written")
        backlog = Backlog(workspace)
        for t in task_dicts:
            backlog.add_task(
                t.get("title", "Untitled"),
                t.get("description", ""),
                depends_on=t.get("depends_on", []),
            )
        print(f"[{lead.name} | Eng Manager] Backlog ready: {len(task_dicts)} tasks\n{backlog.summary()}\n")

        coordinator = self.coordinators[0] if self.coordinators else None

        # ── Build loop ────────────────────────────────────────────────────────
        sprint = 0
        test_results: list[dict] = []
        completed_this_round: list = []
        skills_invoked: list[dict] = []
        forced_completions: list[str] = []  # 1.4: track force-completed tasks
        security_warnings: list[str] = []  # 2.7: track skipped security checks

        def _process_task(dev, task):
            active_dev = dev
            local_skills: list[dict] = []
            log_entries: list[tuple] = []
            local_traces: list[dict] = []

            if coordinator:
                with self._coordinator_lock:
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
                        local_skills.append({"task": task.title, "skill": skill_name, "triggered_by": coordinator.name})
                        task.description = (
                            f"--- Skill: {skill_name} ---\n{skill_output}\n\n"
                            f"--- Original Task ---\n{task.description}"
                        )
                    except Exception as e:
                        print(f"[{coordinator.name} | Coordinator] Skill '{skill_name}' failed: {e}")

                elif mode == "specialist":
                    role_desc = approach["specialist_role"]
                    print(f"[{coordinator.name} | Coordinator] Spawning specialist: {role_desc[:60]}")
                    with self._coordinator_lock:
                        active_dev = coordinator.spawn_specialist(role_desc)
                    active_dev.workspace = workspace
                    active_dev.memory_context = memory_ctx

            approved = False
            for attempt in range(1, MAX_REJECTIONS + 2):
                print(f"[{active_dev.name}] Implementing: {task.title} (attempt {attempt})")
                t0 = time.time()
                active_dev.implement_task(task, workspace)
                impl_elapsed = time.time() - t0
                local_traces.append({
                    "agent": active_dev.name,
                    "step": f"implement:{task.title}",
                    "attempt": attempt,
                    "duration_s": round(impl_elapsed, 2),
                    "tokens": active_dev._token_usage.copy(),
                })

                if not coordinator:
                    approved = True
                    break

                print(f"[{coordinator.name} | Coordinator] Reviewing: {task.title}")
                with self._coordinator_lock:
                    review = coordinator.review_task(task, workspace)

                if review.get("skill_audit"):
                    local_skills.append({"task": task.title, "skill": "security_audit", "triggered_by": coordinator.name})

                if review["approved"]:
                    approved = True
                    print(f"[{coordinator.name} | Coordinator] Approved: {task.title}")
                    log_entries.append(("success", task.title, f"Approved on attempt {attempt}", review["feedback"][:200]))
                    break

                print(f"[{coordinator.name} | Coordinator] Rejected (attempt {attempt}): {review['feedback'][:100]}...")
                log_entries.append(("rejection", task.title, review["feedback"][:300], f"Attempt {attempt} of {MAX_REJECTIONS + 1}"))

                if attempt <= MAX_REJECTIONS:
                    updated_desc = (
                        task.description
                        + f"\n\n--- Coordinator Feedback (attempt {attempt}) ---\n"
                        + review["feedback"]
                    )
                    backlog.update_task(task.id, description=updated_desc)

            # 1.4: Track force-completions
            was_force_completed = not approved
            if was_force_completed:
                print(f"[Coordinator] Max attempts reached for '{task.title}' — force-completing")

            return task, local_skills, log_entries, local_traces, was_force_completed

        while backlog.get_pending() and sprint < MAX_BUILD_SPRINTS:
            if self._cancel_requested:
                print("[Squad] Build cancelled by request — stopping after current sprint")
                break

            sprint += 1
            print(f"[Squad] ── Sprint {sprint} ─────────────────────────────")
            completed_this_round = []

            dev_task_pairs: list[tuple] = []
            for dev in self.developers:
                if self._cancel_requested:
                    break
                task = lead.assign_next_task(backlog, dev.name)
                if task is None:
                    break
                dev_task_pairs.append((dev, task))

            if not dev_task_pairs:
                break

            max_workers = max(1, len(dev_task_pairs))
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {
                    pool.submit(_process_task, dev, task): (dev, task)
                    for dev, task in dev_task_pairs
                }
                for future in as_completed(futures):
                    task, local_skills, log_entries, local_traces, was_force_completed = future.result()
                    # 1.4: Use appropriate complete method
                    if was_force_completed:
                        backlog.force_complete_task(task.id)
                        forced_completions.append(task.title)
                    else:
                        backlog.complete_task(task.id)
                    completed_this_round.append(task)
                    skills_invoked.extend(local_skills)
                    agent_traces.extend(local_traces)
                    for entry_type, title, rationale, outcome in log_entries:
                        decision_log.record(spec.name, entry_type, title, rationale, outcome)

            for sdet in self.sdets:
                for task in completed_this_round:
                    print(f"[{sdet.name}] Testing: {task.title}")
                    t0 = time.time()
                    tr = sdet.test_task(task, workspace)
                    elapsed = time.time() - t0
                    test_results.append({"task": task.title, **tr})
                    agent_traces.append({"agent": sdet.name, "step": f"test:{task.title}", "duration_s": round(elapsed, 2), "tokens": sdet._token_usage.copy()})
                    print(f"[{sdet.name}] Results: {tr['passed']} passed, {tr['failed']} failed")
                    # 2.7: Track skipped security checks
                    if tr.get("security_check_skipped"):
                        security_warnings.append(f"Security scan skipped for task: {task.title}")
                    if tr.get("lint_check_skipped"):
                        security_warnings.append(f"Lint check skipped for task: {task.title}")

            print(f"\n{backlog.summary()}\n")

        _checkpoint("after_build")

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

        print(f"\n[Squad] Build complete — {len(files_created)} files, {total_passed} tests passed, {total_failed} failed")

        # Step 6: Constitutional safety review
        safety_result: dict = {"safe": True, "findings": "No safety reviewer in squad.", "warnings": []}
        safety_reviewer = self.safety_reviewers[0] if self.safety_reviewers else None
        if safety_reviewer:
            safety_reviewer.workspace = workspace
            safety_reviewer.memory_context = memory_ctx
            print(f"\n[{safety_reviewer.name} | Safety] Running constitutional review...")
            t0 = time.time()
            safety_result = safety_reviewer.review_safety(workspace)
            elapsed = time.time() - t0
            timings["safety_review"] = elapsed
            agent_traces.append({"agent": safety_reviewer.name, "step": "review_safety", "duration_s": round(elapsed, 2), "tokens": safety_reviewer._token_usage.copy()})
            verdict_label = "CONSTITUTIONAL" if safety_result["safe"] else "VIOLATIONS FOUND"
            print(f"[{safety_reviewer.name} | Safety] {verdict_label}: {safety_result['findings'][:200]}...\n")
            decision_log.record(
                spec.name,
                "success" if safety_result["safe"] else "rejection",
                "Constitutional safety review",
                safety_result["findings"][:300],
                verdict_label,
            )
            _checkpoint("after_safety")

        # Step 7: PM delivery review
        pm_verdict = ""
        if pm:
            # 1.4: Include forced completions in PM report
            force_complete_note = ""
            if forced_completions:
                force_complete_note = (
                    f"\n\n⚠️ IMPORTANT: The following tasks were force-completed after "
                    f"reaching the maximum coordinator rejection limit. They may contain "
                    f"incomplete or substandard implementations:\n"
                    + "\n".join(f"  - {t}" for t in forced_completions)
                )
            print(f"[{pm.name} | PM] Reviewing delivery against acceptance criteria...")
            t0 = time.time()
            pm_verdict = pm.review_delivery(workspace)
            elapsed = time.time() - t0
            timings["pm_review"] = elapsed
            agent_traces.append({"agent": pm.name, "step": "review_delivery", "duration_s": round(elapsed, 2), "tokens": pm._token_usage.copy()})
            if force_complete_note:
                pm_verdict = force_complete_note + "\n\n" + pm_verdict
            print(f"[{pm.name} | PM] Verdict: {pm_verdict[:200]}...\n")
            decision_log.record(spec.name, "outcome", "PM delivery review", pm_verdict[:300])

        # 4.7: Aggregate token usage and cost estimate
        total_input = sum(m._token_usage.get("input", 0) for m in self.members)
        total_output = sum(m._token_usage.get("output", 0) for m in self.members)
        cost_usd = (total_input / 1_000_000) * cfg.COST_PER_MTK_IN + (total_output / 1_000_000) * cfg.COST_PER_MTK_OUT

        # Collect all warnings
        all_warnings = list(security_warnings) + list(safety_result.get("warnings", []))
        if forced_completions:
            all_warnings.append(f"{len(forced_completions)} task(s) force-completed: {', '.join(forced_completions)}")

        timings["total"] = round(time.time() - build_start, 2)

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
            "forced_completions": forced_completions,
            "warnings": all_warnings,
            "token_usage": {"input": total_input, "output": total_output},
            "cost_estimate_usd": round(cost_usd, 4),
            "timings": timings,
            "agent_traces": agent_traces,
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

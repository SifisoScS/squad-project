import json
import argparse
from team import Team
from team.project import ProjectSpec

# 3.8: Accept project spec from CLI args or a JSON file
parser = argparse.ArgumentParser(description="Autonomous software factory powered by Claude AI")
parser.add_argument(
    "--mode",
    choices=["build", "simulate"],
    default="build",
    help="build: autonomous project builder | simulate: sprint simulation (default: build)",
)
parser.add_argument("--sprints", type=int, default=3, help="Sprints for simulate mode (default: 3)")

# 3.8: Spec input modes
spec_group = parser.add_argument_group("Project spec (for build mode)")
spec_group.add_argument("--spec", help="Path to a project spec JSON file (see spec.example.json)")
spec_group.add_argument("--name", help="Project name (e.g. task-manager-api)")
spec_group.add_argument("--description", help="Project description")
spec_group.add_argument("--stack", nargs="+", help="Tech stack items (e.g. Python FastAPI SQLite)")
spec_group.add_argument("--timeout", type=int, default=1800, help="Build timeout in seconds (default: 1800)")

args = parser.parse_args()


def _load_spec_from_args() -> ProjectSpec:
    """Load ProjectSpec from --spec file, --name/--description/--stack flags, or built-in example."""
    if args.spec:
        path = __import__("pathlib").Path(args.spec)
        if not path.exists():
            parser.error(f"Spec file not found: {args.spec}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            parser.error(f"Failed to read spec file: {e}")
        return ProjectSpec(
            name=data["name"],
            description=data["description"],
            tech_stack=data["tech_stack"],
            build_timeout_seconds=data.get("build_timeout_seconds", args.timeout),
            human_checkpoints=data.get("human_checkpoints", []),
        )

    if args.name or args.description or args.stack:
        missing = [f for f, v in [("--name", args.name), ("--description", args.description), ("--stack", args.stack)] if not v]
        if missing:
            parser.error(f"When using CLI flags, all three are required: {', '.join(missing)}")
        return ProjectSpec(
            name=args.name,
            description=args.description,
            tech_stack=args.stack,
            build_timeout_seconds=args.timeout,
        )

    # Default built-in example
    return ProjectSpec(
        name="task-manager-api",
        description="""
        Build a REST API for a task management application using Python and FastAPI.

        Features required:
        - CRUD operations for tasks: create, read, update, delete
        - Each task has: id, title, description, status (todo/in_progress/done), priority (low/medium/high)
        - JWT authentication: register, login, token-based access
        - SQLite database with SQLAlchemy ORM
        - Input validation with Pydantic models
        - Full pytest test suite with at least 80% coverage

        Non-functional requirements:
        - Clean project structure with separate modules for models, routes, auth, database
        - All endpoints return consistent JSON responses
        - Proper HTTP status codes (200, 201, 400, 401, 404, 422)
        - Requirements.txt with all dependencies pinned
        """,
        tech_stack=["Python", "FastAPI", "SQLite", "SQLAlchemy", "Pydantic", "python-jose", "pytest", "httpx"],
        build_timeout_seconds=args.timeout,
    )


if args.mode == "build":
    spec = _load_spec_from_args()
    team = Team.default()
    report = team.build_project(spec)

    print("\n" + "=" * 60)
    print("SQUAD SHIP REPORT")
    print("=" * 60)
    print(json.dumps(report, indent=2))

else:
    # ── SPRINT SIMULATION MODE ────────────────────────────────────────────────
    from agents import Developer, SDET, TeamLead, ProductManager

    pm_roles = [
        "Own the product vision and success metrics for this sprint",
        "Ensure every sprint goal maps to a user outcome, not just a feature",
        "Represent the voice of the customer in squad discussions",
        "Review sprint deliverables against acceptance criteria",
    ]
    developer_roles = [
        "Ship production-quality code that moves the squad's OKRs forward",
        "Write clean, maintainable, testable code — bias toward simplicity",
        "Participate in code reviews with a quality-first mindset",
        "Collaborate with QA to make every feature testable from day one",
    ]
    sdet_roles = [
        "Translate acceptance criteria from the PM into automated test cases",
        "Execute tests and surface quality issues early in the sprint",
        "Analyze results and report defects with clear reproduction steps",
        "Champion testability as a first-class design concern",
    ]
    eng_manager_roles = [
        "Remove impediments the moment they're raised — blockers kill velocity",
        "Keep the squad focused on sprint goals and shielded from noise",
        "Facilitate squad ceremonies and track sprint OKR progress",
        "Coach engineers and run performance retrospectives",
    ]

    pm = ProductManager("Jordan Lee", pm_roles)
    developer1 = Developer("Priya Patel", developer_roles)
    developer2 = Developer("Marcus Johnson", developer_roles)
    sdet1 = SDET("David Lee", sdet_roles)
    eng_manager = TeamLead("Michael Brown", eng_manager_roles)

    team = Team("Product Squad", [pm, developer1, developer2, sdet1, eng_manager])
    team.set_goals([
        "Ship user authentication with JWT — OKR: 0 unauthorized access incidents",
        "Launch product catalog API — OKR: <200 ms p99 latency on read endpoints",
        "Achieve 85% automated test coverage — OKR: <2 production incidents per quarter",
        "Resolve all P0/P1 bugs — OKR: customer satisfaction score ≥ 4.5/5",
    ])

    for sprint in range(args.sprints):
        print(f"\n{'=' * 60}")
        print(f"SPRINT {sprint + 1}")
        print("=" * 60)

        print("\n--- Daily Standup ---")
        synthesis = team.daily_standup()
        print(f"\nTeam Lead synthesis:\n{synthesis}\n")

        print("\n--- Working on Tasks ---")
        team.work_on_tasks()

        print("\n--- Code Review ---")
        team.code_review()

        print("\n--- Retrospective ---")
        retro = team.retrospective()
        print(f"\nRetrospective:\n{retro}\n")

    print(f"\n{'=' * 60}")
    print("FINAL PERFORMANCE REPORT")
    print("=" * 60)
    report = team.get_performance()
    print(json.dumps(report, indent=2))

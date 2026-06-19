# Multi-Claude Agents — Autonomous Software Factory

An autonomous, multi-agent software development system powered by Claude AI.
Give it a plain-English project description; the squad designs the architecture, writes the code,
tests it, safety-reviews it, and delivers a working project — end to end, no hand-holding.

**Two ways to use it:**
- **Mission Control UI** — browser-based dashboard with live streaming, pipeline progress, and build reports
- **CLI** — run directly from the terminal for scripted / headless pipelines

---

## Quick Start

**Requirements:** Python 3.11+, Anthropic API key

```bash
# 1. Clone
git clone <repo-url>
cd squad-project

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux

# Edit .env and set your Anthropic API key:
ANTHROPIC_API_KEY=sk-ant-...
```

### Option A — Web UI (recommended)

```bash
python -m uvicorn api.main:app --port 8000
```

Open **http://localhost:8000** → click **New Build** → describe your project → **Launch Squad**.

### Option B — CLI

```bash
# From a spec file
python main.py --spec spec.example.json

# Inline flags
python main.py --name my-api --description "REST API for task management" --stack Python FastAPI SQLite pytest

# Default built-in example (task-manager-api)
python main.py --mode build
```

---

## How It Works

### The 7-step pipeline

```
ProjectSpec (plain-English description + tech stack)
        │
        ▼
┌──────────────────┐
│  Jordan Lee      │  Step 1 — writes PRD.md
│  Product Manager │  user stories + acceptance criteria + success metrics
└────────┬─────────┘
         │  PRD.md
         ▼
┌──────────────────┐
│  Alex Chen       │  Step 2 — reads PRD, writes ARCHITECTURE.md
│  Architect       │  + backlog_tasks.json (6–10 ordered tasks)
└────────┬─────────┘
         │  backlog_tasks.json
         ▼
┌──────────────────┐
│  Michael Brown   │  Step 3 — loads backlog, sequences tasks
│  Eng Manager     │
└────────┬─────────┘
         │  for each task:
         ▼
┌──────────────────┐   suggest_approach()   ┌─────────────────────────┐
│  Sarah Kim       │ ─────────────────────► │  Skills Library (115)   │
│  Coordinator     │   generalist / skill / │  decompose, tech_spike, │
└────────┬─────────┘   specialist           │  security_audit, etc.   │
         │                                  └─────────────────────────┘
         │  assign task
         ▼
┌──────────┐  ┌──────────────┐
│  Priya   │  │   Marcus     │  Step 4 — implement tasks in parallel
│  Patel   │  │   Johnson    │  (Coordinator quality-gates each one;
│  Senior  │  │   Senior     │   security_audit skill auto-fires on
│  Engineer│  │   Engineer   │   auth/jwt/sql/credential tasks)
└────┬─────┘  └──────┬───────┘
     └────────────┬──┘
                  │  completed tasks
                  ▼
         ┌──────────────────┐
         │  David Lee       │  Step 5 — pytest + bandit + ruff
         │  SDET            │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │  Dr. Amara Wells │  Step 6 — constitutional safety review
         │  Safety Reviewer │  10-principle Safety Constitution
         └────────┬─────────┘  CONSTITUTIONAL or VIOLATIONS FOUND
                  │
                  ▼
         ┌──────────────────┐
         │  Jordan Lee      │  Step 7 — delivery review
         │  Product Manager │  PASS/FAIL each acceptance criterion
         └──────────────────┘
```

---

## Mission Control UI

The web UI gives you full visibility into every build in real time.

### Layout

| Area | Description |
|------|-------------|
| **Header** | Live stats: total builds, active builds, registered skills |
| **Left nav** | Builds · New Build · Skills · Workspaces |
| **Build sidebar** | Searchable, filterable list of all builds with status dots |
| **Build detail** | Pipeline stepper + live log + report + trace tabs |

### Build detail view

**Pipeline stepper** — 7 stages with live status:

```
PRD  ──  Architecture  ──  Development  ──  Testing  ──  Safety  ──  Delivery  ──  Report
 ✓            ✓                 ●               ○           ○          ○            ○
```
`✓` = complete · `●` = active (pulsing) · `○` = pending

**Live Metrics Ribbon** — events, tokens, cost, and current stage update in real time above the log.

**Structured log rows** — every line is parsed and colour-coded by agent:

```
HH:MM:SS  │  [Jordan Lee]  │  Writing PRD.md with 6 user stories…
          │  (purple)      │
HH:MM:SS  │  [Alex Chen]   │  Architecture decision: SQLite over Postgres for…
          │  (indigo)      │
```

| Agent | Colour |
|-------|--------|
| Product Manager | Purple |
| Architect | Indigo |
| Developer | Cyan |
| Coordinator | Teal |
| SDET / QA | Green |
| Safety Reviewer | Orange |
| System | Grey |

**Checkpoint banner** — when `human_checkpoints` are configured, a blue banner pauses the build
and shows an **Approve & Continue** button.

**Report tab** — structured summary after completion:
- Hero card (status + sprint count + constitutional verdict)
- Metric cards (test pass rate, tokens, cost, skills invoked)
- Test progress bar
- Safety findings
- Skills tag cloud
- Force-completed task warnings
- PM delivery review text

**Trace tab** — per-agent performance bar chart. Toggle between **Duration** and **Tokens**.
Bottleneck agent is called out with % of total runtime.

**Floating Build Widget** — bottom-right overlay during active builds showing current stage,
progress bar, elapsed time, and event count.

---

## The Squad

| Agent | Name | Role | Key method |
|-------|------|------|-----------|
| **ProductManager** | Jordan Lee | Owns "what" and "why" — voice of the customer | `define_product_requirements()`, `review_delivery()` |
| **Architect** | Alex Chen | Turns PRD into system design + ordered backlog | `design_project()` |
| **Coordinator** | Sarah Kim | Quality gate per task; routes to skill or specialist | `review_task()`, `suggest_approach()` |
| **Developer** | Priya Patel | Implements tasks; benefits from skill pre-processing | `implement_task()` |
| **Developer** | Marcus Johnson | Implements tasks in parallel with Priya | `implement_task()` |
| **SDET** | David Lee | pytest + bandit + ruff; translates AC into tests | `test_task()` |
| **TeamLead** | Michael Brown | Loads backlog, sequences tasks, removes blockers | `assign_next_task()` |
| **SafetyReviewer** | Dr. Amara Wells | Constitutional review of the full codebase | `review_safety()` |

All agents share a `BaseAgent` foundation:
- `think()` — single-turn reasoning (no tools)
- `act()` — multi-turn plan-act-observe tool loop (up to 15 iterations)
- `invoke_skill(name, task)` — call any of the 115 library skills
- Prompt caching on system prompts to reduce API cost
- Token usage tracking per agent (aggregated into build cost estimate)

---

## Skills Library

115 reusable Claude capabilities across 16 domains.

```python
# Inside any agent method
result = self.invoke_skill("system_design", task_description)
result = self.invoke_skill("threat_model", feature_description)

# Standalone
from skills import SkillRegistry

result = SkillRegistry.invoke("capacity_plan", "Social media feed for 10M DAU")

# Chain skills (output of each feeds the next)
results = SkillRegistry.chain(["decompose", "system_design", "adr"], "Design a payment service")

# Compose with dependency resolution (topological sort)
results = SkillRegistry.compose(["adr", "system_design", "decompose"], "Design a payment service")

# List / filter
for s in SkillRegistry.list_skills(category="security"):
    print(f"{s.name}: {s.description}")
```

### Discovery — 4 skills
| Skill | What it does |
|-------|-------------|
| `decompose` | Break a complex task into ordered atomic sub-tasks with acceptance criteria |
| `tech_spike` | Evaluate 2–4 options and recommend one with explicit trade-offs |
| `user_story_map` | Build a story map with epics, walking skeleton, and release slices |
| `problem_framing` | Frame the problem space using Jobs-to-be-Done before committing to a solution |

### Architecture — 7 skills
| Skill | What it does |
|-------|-------------|
| `system_design` | Design a distributed system: components, data flow, scaling, failure modes |
| `adr` | Write an Architecture Decision Record with context, options, and consequences |
| `microservice_split` | Decompose a monolith into bounded-context microservices with seam analysis |
| `api_contract` | OpenAPI-first API contract: endpoints, schemas, error codes, versioning |
| `capacity_plan` | Estimate traffic, storage, compute, bandwidth, and monthly cost envelope |
| `multi_tenant` | Isolation model (silo/bridge/pool), data partitioning, tenant routing, lifecycle, quotas |
| `backwards_compat` | Change classification table, API versioning strategy, deprecation lifecycle (min 6 months) |

### Frontend — 16 skills
| Skill | What it does |
|-------|-------------|
| `component_design` | Design component hierarchy with props/state contracts and composition patterns |
| `state_design` | Decide what state lives where (local / lifted / global store / server cache) |
| `a11y_audit` | WCAG 2.1 AA audit — criterion, severity, location, and exact fix for each finding |
| `bundle_audit` | Analyse bundle size, flag heavy deps, produce prioritised optimisation plan |
| `perf_web` | Audit Core Web Vitals (LCP, INP, CLS) with root causes and specific fixes |
| `landing_page` | High-converting React landing page with 6-section narrative and Framer Motion reveals |
| `form_design` | React Hook Form + Zod forms with all 8 required UX states and blur-first validation |
| `animation` | Framer Motion animations — stagger, scroll-triggered, exit, parallax — GPU-only transforms |
| `responsive_layout` | Mobile-first layouts using `auto-fill + minmax`, `clamp()` typography, container queries |
| `design_system` | Three-tier token architecture (primitive → semantic → component), 4px spacing scale |
| `dark_mode` | Flash-free dark mode with CSS variables, `[data-theme]`, SSR blocking script, 3-option toggle |
| `auth_ui` | Branded auth flows (split-screen / full-bleed / dark-first) with Framer Motion transitions |
| `state_management_react` | Zustand slice pattern with selectors, Immer, Context + useReducer |
| `accessibility_react` | WCAG 2.1 AA — semantic HTML, keyboard interaction, ARIA sparingly, jest-axe |
| `l10n_i18n` | BCP-47 locale codes, message catalogue structure, ICU pluralisation, RTL support |
| `performance_budget` | Core Web Vitals budgets (LCP, INP, CLS, TTFB), Lighthouse CI enforcement |

### Backend — 14 skills
| Skill | What it does |
|-------|-------------|
| `api_design` | Design RESTful endpoints: naming, verbs, status codes, pagination, idempotency |
| `caching_strategy` | Design cache topology, TTL policy, and event-based invalidation |
| `rate_limiting` | Design throttling: algorithm, tier structure, headers, and enforcement layer |
| `background_jobs` | Design worker architecture: queues, retries, DLQ, idempotency, observability |
| `error_handling` | Error taxonomy, propagation rules, logging contract, circuit breaker |
| `auth_backend` | Argon2 hashing, jose JWT, access + refresh token rotation, httpOnly cookies, RBAC |
| `validation_node` | Zod `validate(schema, part)` middleware factory, `safeParse()`, `z.coerce` for query params |
| `caching_node` | Cache-aside `withCache<T>()`, Redis key naming, TTL strategy, single-flight |
| `logging_node` | Pino + AsyncLocalStorage request correlation, `getLogger()` child logger, redact config |
| `testing_backend_node` | Vitest + Supertest, feature-organized structure, unit vs integration test split |
| `database_schema` | Primary key selection, naming conventions, relationship patterns, composite index order |
| `prisma_orm` | Prisma schema conventions, `select` over `include`, `$transaction`, N+1 prevention |
| `feature_flag` | Flag taxonomy (release/experiment/ops/permission), rollout strategy, cleanup lifecycle |
| `genai_integration` | RAG pipeline design, model selection, prompt architecture, token budget, failure handling |

### Data — 7 skills
| Skill | What it does |
|-------|-------------|
| `data_model` | Design relational/document model: entities, indexes, constraints, migration path |
| `query_optimize` | Diagnose slow queries with EXPLAIN analysis and produce optimised rewrites |
| `etl_design` | Design ETL/ELT pipeline: idempotency, error handling, DLQ, scheduling |
| `data_quality` | Define quality rules (completeness, validity, freshness) and alerting thresholds |
| `ml_pipeline` | Design ML training and serving: data prep, evaluation gate, rollout, monitoring |
| `db_migration` | Generate safe reversible up/down schema migrations with risk flags |
| `db_replication` | Topology options, connection pooling, application-layer routing, replication lag, failover |

### Mobile — 3 skills
| Skill | What it does |
|-------|-------------|
| `mobile_arch` | Architecture for iOS/Android/RN/Flutter: navigation, state, offline strategy |
| `offline_sync` | Offline-first sync design with conflict resolution and optimistic UI |
| `app_security` | OWASP Mobile Top 10 audit: storage, transport, auth, binary protections |

### DevOps — 8 skills
| Skill | What it does |
|-------|-------------|
| `dockerfile` | Production-ready multi-stage Dockerfile: non-root, pinned, minimal surface |
| `ci_design` | CI/CD pipeline: quality gates, environment promotion, secrets, rollback |
| `k8s_deploy` | Kubernetes manifests: Deployment, Service, HPA, PDB, NetworkPolicy |
| `infra_as_code` | Terraform module: resources, variables, outputs, state backend, tagging |
| `observability` | Observability stack: RED/USE metrics, structured logs, traces, alerting |
| `incident_response` | Runbook with severity tiers, alert inventory, triage checklist, comms templates |
| `cost_optimisation` | Cloud cost audit: immediate wins, short-term reductions, architecture changes, savings table |
| `chaos_engineering` | Chaos experiment design: steady state, blast radius, abort conditions, GameDay plan |

### Security — 6 skills
| Skill | What it does |
|-------|-------------|
| `security_audit` | OWASP Top 10 audit with file-and-line violations and concrete fixes |
| `threat_model` | STRIDE threat model: threats, risk ratings, and mitigations |
| `compliance_check` | GDPR / SOC 2 / HIPAA gap analysis with prioritised remediation list |
| `secret_management` | Secret storage, access control, rotation policy, and compromise playbook |
| `secret_rotation` | Rotation runbook: trigger conditions, pre-rotation checklist, zero-downtime steps, rollback |
| `data_privacy` | GDPR data inventory, subject rights (SAR, erasure, portability), consent, breach response |

### Quality — 8 skills
| Skill | What it does |
|-------|-------------|
| `test_coverage` | Identify coverage gaps and generate missing tests (happy path + edge cases) |
| `explain` | Explain code in plain language — the WHY, not the WHAT |
| `debug` | Root-cause diagnosis with minimal fix — never suppress, never mask |
| `refactor` | Refactor for SOLID/clarity with zero behaviour change |
| `load_test` | Design load test scenarios: ramp profiles, SLOs, failure criteria, tool choice |
| `postmortem` | Blameless post-incident review: timeline, 5 Whys, what went well/poorly, action items |
| `contract_testing` | Pact-pattern consumer-driven contract tests: interaction JSON, provider state, CI integration |
| `flaky_test_diagnosis` | Root cause classification, reproduction steps, fix plan, prevention policy |

### Documentation — 4 skills
| Skill | What it does |
|-------|-------------|
| `api_docs` | OpenAPI-compliant endpoint docs — all params, all response codes |
| `changelog` | Keep-a-Changelog entry: user-visible language, no file names |
| `readme_write` | Comprehensive README: quick start, config, usage examples, troubleshooting |
| `runbook` | Operational runbook: per-alert diagnosis steps and ordered remediation |

### Integration — 4 skills
| Skill | What it does |
|-------|-------------|
| `webhook_design` | Webhook system: envelope, HMAC signing, retry policy, DLQ, consumer guide |
| `messaging_design` | Message queue / event streaming: topics, consumers, ordering, DLQ, schema evolution |
| `payment_design` | Payment integration: provider, PCI scope, idempotency, reconciliation, disputes |
| `oauth_design` | OAuth 2.0 / OIDC: flow selection, token handling, PKCE, provider config |

### Realtime — 3 skills
| Skill | What it does |
|-------|-------------|
| `websocket_design` | WebSocket/SSE system: connection lifecycle, rooms, presence, horizontal scaling |
| `event_sourcing` | Event sourcing + CQRS: event store, aggregates, projections, replay |
| `stream_processing` | Stream pipeline: sources, transforms, windowing, fault tolerance, monitoring |

### Workflow — 6 skills
| Skill | What it does |
|-------|-------------|
| `git_workflow` | Branch naming, Conventional Commits, trunk-based vs Gitflow, rebase local / merge PRs |
| `pull_request` | 5-component PR anatomy (title, why, how, test plan, screenshots), scope discipline |
| `code_review` | 5-layer review hierarchy (correctness → security → performance → design → style) |
| `debugging` | 7-step root-cause process: reproduce → read error → narrow → hypothesise → verify → fix |
| `refactoring` | Safety-net-first, commit at every green, high-churn files first |
| `technical_debt` | Fowler's debt quadrant, `Priority = Impact × Frequency × Risk`, DEBT.md |

### Next.js — 9 skills
`app_router` · `server_components` · `nextjs_middleware` · `api_routes_nextjs` · `nextjs_performance` · `typescript_patterns_nextjs` · `nextauth` · `data_fetching_nextjs` · `server_actions_nextjs`

### Flutter — 8 skills
`flutter_ui` · `flutter_state` · `flutter_navigation` · `flutter_networking` · `flutter_animations` · `flutter_forms` · `flutter_architecture` · `flutter_testing`

### Blazor — 8 skills
`blazor_components` · `blazor_forms` · `blazor_state` · `blazor_auth` · `blazor_js_interop` · `blazor_data` · `blazor_routing` · `blazor_performance`

---

## REST API

The FastAPI server exposes the full pipeline over HTTP. All mutating endpoints require a `Bearer` token when `API_SECRET_KEY` is set in the environment.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/build` | Start a new build |
| `GET` | `/build/{id}` | Build status + final report |
| `GET` | `/build/{id}/stream` | SSE stream of agent output |
| `GET` | `/build/{id}/events` | Full event log as JSON |
| `GET` | `/build/{id}/trace` | Per-agent timing + token trace |
| `DELETE` | `/build/{id}` | Cancel a running build |
| `POST` | `/build/{id}/approve` | Approve a human-in-the-loop checkpoint |
| `GET` | `/builds` | Paginated build list (`?page=1&page_size=25&status=running`) |
| `POST` | `/skill/invoke` | Invoke a single skill synchronously |
| `GET` | `/skills` | List all 115 registered skills |
| `GET` | `/skills/categories` | Skill category list |
| `GET` | `/workspaces` | List generated project workspaces |
| `DELETE` | `/workspace/{name}` | Delete a workspace |
| `GET` | `/health` | Liveness probe with running build count |
| `GET` | `/` | Web UI |

### Start a build via API

```bash
curl -X POST http://localhost:8000/build \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-key" \
  -d '{
    "name": "task-manager-api",
    "description": "Build a REST API for task management with JWT auth, CRUD, and SQLite",
    "tech_stack": ["Python", "FastAPI", "SQLite", "pytest"]
  }'
```

### Stream live output

```bash
curl -N http://localhost:8000/build/{id}/stream
```

### Invoke a skill

```bash
curl -X POST http://localhost:8000/skill/invoke \
  -H "Content-Type: application/json" \
  -d '{"skill_name": "threat_model", "task": "OAuth flow for a banking app"}'
```

---

## Configuration

All settings live in `config.py` and are controlled by environment variables. Copy `.env.example` to `.env` and edit.

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | **Required.** Your Anthropic API key |
| `SQUAD_MODEL` | `claude-sonnet-4-6` | Claude model for all agents |
| `API_SECRET_KEY` | *(empty)* | Bearer token for API auth. Auth disabled when empty |
| `ALLOWED_ORIGINS` | `http://localhost:8000` | CORS allowed origins (comma-separated) |
| `WORKSPACE_ROOT` | `workspace` | Root directory for generated projects |
| `MAX_ITERATIONS` | `15` | Max tool-loop iterations per agent call |
| `MAX_RETRIES` | `3` | API retry attempts on transient errors |
| `MAX_BUILD_SPRINTS` | `10` | Build stops after this many sprints |
| `MAX_REJECTIONS` | `2` | Coordinator rejections before force-complete |
| `BUILD_TIMEOUT_SECONDS` | `1800` | Build hard timeout (30 min) |
| `RETRY_BASE_DELAY` | `2.0` | Exponential backoff base delay (seconds) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG / INFO / WARNING) |
| `SSL_NO_VERIFY` | `false` | Disable SSL verification (corporate proxies) |
| `SSL_CERT_FILE` | *(empty)* | Path to corporate CA bundle |

### Human-in-the-loop checkpoints

Add `human_checkpoints` to your `ProjectSpec` to pause the build for review:

```python
ProjectSpec(
    name="payment-api",
    description="...",
    tech_stack=["Python", "FastAPI"],
    human_checkpoints=["after_prd", "after_architecture"],
)
```

Valid values: `after_prd` · `after_architecture` · `after_build` · `after_safety`

When a checkpoint is reached, the build status changes to `awaiting_review`, the SSE stream emits a `checkpoint` event, and the UI shows the **Approve & Continue** banner.

---

## Project Structure

```
squad-project/
├── agents/
│   ├── base.py              # BaseAgent: think() + act() + invoke_skill(); token tracking
│   ├── product_manager.py   # Writes PRD.md; reviews delivery against acceptance criteria
│   ├── architect.py         # Reads PRD; writes ARCHITECTURE.md + backlog_tasks.json
│   ├── coordinator.py       # Quality gate; suggest_approach() → skill/specialist/generalist
│   ├── developer.py         # Implements tasks; uses skill pre-processing output
│   ├── sdet.py              # pytest + bandit + ruff; translates AC into tests
│   ├── team_lead.py         # Loads backlog, assigns tasks, removes blockers
│   ├── safety_reviewer.py   # Constitutional review of the full codebase
│   └── __init__.py
├── api/
│   ├── main.py              # FastAPI app — all endpoints, SSE generator, build runner
│   ├── models.py            # Pydantic request/response models with validation
│   ├── auth.py              # Bearer token auth dependency
│   ├── store.py             # SQLite persistence (build records survive restarts)
│   └── static/
│       └── index.html       # Mission Control UI (self-contained, no CDN)
├── skills/
│   ├── __init__.py          # Loads the full library on import
│   ├── registry.py          # Skill + SkillAgent + SkillRegistry; chain() + compose()
│   └── library/
│       ├── __init__.py      # Imports all 16 category modules
│       ├── discovery.py     # 4 skills
│       ├── architecture.py  # 7 skills
│       ├── frontend.py      # 16 skills
│       ├── backend.py       # 14 skills
│       ├── data.py          # 7 skills
│       ├── mobile.py        # 3 skills
│       ├── devops.py        # 8 skills
│       ├── security.py      # 6 skills
│       ├── quality.py       # 8 skills
│       ├── documentation.py # 4 skills
│       ├── integration.py   # 4 skills
│       ├── realtime.py      # 3 skills
│       ├── workflow.py      # 6 skills
│       ├── nextjs.py        # 9 skills
│       ├── flutter.py       # 8 skills
│       └── blazor.py        # 8 skills
├── tools/
│   ├── file_tools.py        # write_file, read_file, list_files, create_directory
│   ├── code_tools.py        # run_python, run_tests (pytest), run_bandit, run_ruff
│   ├── registry.py          # Tool schemas + dispatcher; role → tool mapping
│   └── __init__.py
├── team/
│   ├── team.py              # Team orchestrator: 7-step pipeline + sprint simulation
│   ├── project.py           # ProjectSpec dataclass (name, description, tech_stack, checkpoints)
│   ├── backlog.py           # Task dataclass + JSON-persisted Backlog; depends_on support
│   └── __init__.py
├── memory/
│   ├── decision_log.py      # Cross-project memory: records tech choices, rejections, outcomes
│   └── __init__.py
├── utils/
│   └── logging.py           # Structured logger factory (get_logger); UTF-8 safe on Windows
├── workspace/               # Created at runtime — one subdirectory per project
│   └── {project-name}/
│       ├── PRD.md
│       ├── ARCHITECTURE.md
│       ├── backlog_tasks.json
│       └── <generated source + test files>
├── config.py                # Central config — all settings as env-var-backed attributes
├── main.py                  # CLI entry point — --mode build|simulate, --spec, --name, etc.
├── requirements.txt
├── spec.example.json        # Example project spec for --spec flag
└── .env.example
```

---

## Extending the System

### Add a skill

```python
# skills/library/my_category.py
from skills.registry import Skill, SkillRegistry

SkillRegistry.register(Skill(
    name="graphql_design",
    description="Design a GraphQL schema with types, queries, mutations, and subscriptions",
    category="backend",
    system_prompt="""You are a GraphQL API designer...""",
    tools=["read_file", "write_file"],  # names from tools/registry.py TOOL_DEFINITIONS
    depends_on=["api_contract"],         # optional: runs after api_contract in compose()
))
```

Import the file in `skills/library/__init__.py`. The skill is immediately available in the UI.

### Add an agent

1. Create `agents/my_agent.py` — extend `BaseAgent`, implement `_create_system_prompt()`
2. Add role-specific methods calling `self.think()`, `self.act()`, or `self.invoke_skill()`
3. Export from `agents/__init__.py`
4. Add to `Team.default()` in `team/team.py` and wire into `build_project()`

### Add a tool

1. Implement the function in `tools/file_tools.py` or `tools/code_tools.py`
2. Add the Anthropic tool schema to `TOOL_DEFINITIONS` in `tools/registry.py`
3. Add a dispatch case in `execute_tool()`
4. Add the tool name to the relevant role(s) in `ROLE_TOOLS`

---

## Safety Constitution

The `SafetyReviewer` checks every codebase against these 10 principles before the PM's delivery review:

1. No hardcoded secrets, credentials, API keys, tokens, or passwords in source code
2. No SQL injection vectors — all queries use parameterized statements or an ORM
3. No path traversal vulnerabilities — file paths validated and sandboxed
4. All user input validated and sanitized at system boundaries
5. Authentication and authorization correctly applied to every protected endpoint
6. No logging of sensitive data (passwords, tokens, PII) to any log sink
7. Cryptographic operations use standard vetted libraries — no homegrown crypto
8. Error messages do not leak sensitive system internals to end users
9. No features that enable unauthorized data collection or privacy violation
10. All dependencies explicitly listed; no packages with known critical CVEs

Verdict is either `CONSTITUTIONAL` (safe to ship) or `VIOLATIONS FOUND` (file + line + fix required).

The Safety Reviewer is **read-only by design** (`read_file` + `list_files` only). It can never modify code, only report.

---

## Corporate Network (SSL / Proxy)

If you're on a network with SSL inspection (Zscaler, corporate proxy):

```bash
# Option A — bypass verification (quick, trusted internal networks only)
SSL_NO_VERIFY=true

# Option B — provide your corporate CA bundle (proper solution)
SSL_CERT_FILE=C:\path\to\corporate-ca.pem
```

---

## Key Design Decisions

**PM-first workflow** — The PM writes `PRD.md` before the Architect touches the keyboard. The Architect reads the PRD before designing. Technical design is anchored to user outcomes, not just requirements.

**Skills as first-class citizens** — Skills are isolated Claude invocations with their own expert system prompts. They run in a clean context so they don't pollute the calling agent's conversation history. Any agent can invoke any skill without subclassing.

**Constitutional safety gate** — The Safety Reviewer is read-only. It can never modify code, only report. No other agent can override its verdict.

**Coordinator skill routing** — `suggest_approach()` shows the Coordinator the full skill catalogue and asks it to choose: generalist / skill / specialist. Routing intelligence is an LLM call, not a hardcoded rule.

**Prompt caching** — System prompts are marked `cache_control: ephemeral`. Claude caches them across tool-use loop iterations, reducing token costs for long tasks.

**Context reset per task** — Each `implement_task()` and `test_task()` call resets `self.messages = []`. Agents get a clean context per task rather than accumulating unbounded history.

**Concurrent build guard** — An `asyncio.Lock` prevents two simultaneous `/build` requests from both passing the "is anything running?" check, avoiding `builtins.print` patch corruption.

**Build timeout** — `asyncio.wait_for` enforces `BUILD_TIMEOUT_SECONDS` (default 30 min). Timed-out builds are persisted with status `timeout` so the history is preserved.

**SQLite persistence** — Builds survive server restarts. `api/store.py` persists every completed build; the in-memory `_builds` dict is reloaded from SQLite on startup.

**Atomic backlog writes** — `Backlog._save()` uses `os.replace()` for atomic JSON writes, preventing corruption on interruption.

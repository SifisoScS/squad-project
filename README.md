# Multi-Claude Agents — Autonomous Software Factory

An autonomous, multi-agent software development system powered by Claude AI.
Give it a plain-English project description; it designs the architecture, writes the code,
tests it, safety-reviews it, and delivers a working project — end to end, no hand-holding.

The squad is modelled on three compounding layers:

| Layer | Inspiration | What it adds |
|---|---|---|
| **Silicon Valley product squad** | SVPG empowered-team model | PM-led, OKR-driven, product trio, outcome over output |
| **Anthropic culture** | Anthropic's model spec + RSP | Safety-first hierarchy, constitutional review, honest/low-ego norms |
| **Claude skills library** | Claude Code slash commands | 100 reusable expert capabilities any agent can invoke |

---

## How It Works

Two modes:

| Mode | What it does |
|------|-------------|
| `build` | Autonomous factory — agents design, implement, test, safety-review, and ship a real project on disk |
| `simulate` | Sprint simulation — agents run ceremonies and discuss work in natural language (no files written) |

### Build Mode — the 7-step pipeline

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
│  Sarah Kim       │ ─────────────────────► │  Skills Library (100)   │
│  Coordinator     │   generalist / skill / │  decompose, tech_spike, │
└────────┬─────────┘   specialist           │  security_audit, etc.   │
         │                                  └─────────────────────────┘
         │  assign task
         ▼
┌──────────┐  ┌──────────────┐
│  Priya   │  │   Marcus     │  Step 4 — implement tasks
│  Patel   │  │   Johnson    │  (Coordinator quality-gates each one,
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

## The Squad

`Team.default()` builds this squad. Every member shares the Silicon Valley + Anthropic cultural context.

| Agent | Name | Role | Key method |
|-------|------|------|-----------|
| **ProductManager** | Jordan Lee | Owns "what" and "why" — voice of the customer | `define_product_requirements()`, `review_delivery()` |
| **Architect** | Alex Chen | Turns PRD into system design + ordered backlog | `design_project()` |
| **Coordinator** | Sarah Kim | Quality gate per task; routes to skill or specialist | `review_task()`, `suggest_approach()` |
| **Developer** | Priya Patel | Implements tasks; benefits from skill pre-processing | `implement_task()` |
| **Developer** | Marcus Johnson | Implements tasks in parallel with Priya | `implement_task()` |
| **SDET** | David Lee | pytest + bandit + ruff; translates AC into tests | `test_task()` |
| **TeamLead** | Michael Brown | Loads backlog, sequences tasks, removes blockers | `assign_next_task()`, `facilitate_standup()` |
| **SafetyReviewer** | Dr. Amara Wells | Constitutional review of the full codebase | `review_safety()` |

All agents share a `BaseAgent` foundation with:
- `think()` — single-turn reasoning (no tools)
- `act()` — multi-turn plan-act-observe tool loop (up to 15 iterations)
- `invoke_skill(name, task)` — call any of the 100 library skills
- Prompt caching on system prompts to reduce API cost

---

## Skills Library

100 reusable Claude capabilities across 16 domains. Any agent calls a skill with:

```python
result = self.invoke_skill("system_design", task_description)
result = self.invoke_skill("threat_model", feature_description)
result = self.invoke_skill("decompose", complex_task)
```

The Coordinator's `suggest_approach()` picks the right skill (or specialist) for each task automatically.

### Discovery — 4 skills
| Skill | What it does |
|-------|-------------|
| `decompose` | Break a complex task into ordered atomic sub-tasks with acceptance criteria |
| `tech_spike` | Evaluate 2–4 options and recommend one with explicit trade-offs |
| `user_story_map` | Build a story map with epics, walking skeleton, and release slices |
| `problem_framing` | Frame the problem space using Jobs-to-be-Done before committing to a solution |

### Architecture — 5 skills
| Skill | What it does |
|-------|-------------|
| `system_design` | Design a distributed system: components, data flow, scaling, failure modes |
| `adr` | Write an Architecture Decision Record with context, options, and consequences |
| `microservice_split` | Decompose a monolith into bounded-context microservices with seam analysis |
| `api_contract` | OpenAPI-first API contract: endpoints, schemas, error codes, versioning |
| `capacity_plan` | Estimate traffic, storage, compute, bandwidth, and monthly cost envelope |

### Frontend — 14 skills
| Skill | What it does |
|-------|-------------|
| `component_design` | Design component hierarchy with props/state contracts and composition patterns |
| `state_design` | Decide what state lives where (local / lifted / global store / server cache) |
| `a11y_audit` | WCAG 2.1 AA audit — criterion, severity, location, and exact fix for each finding |
| `bundle_audit` | Analyse bundle size, flag heavy deps, produce prioritised optimisation plan |
| `perf_web` | Audit Core Web Vitals (LCP, INP, CLS) with root causes and specific fixes |
| `landing_page` | High-converting React landing page with 6-section narrative structure and Framer Motion reveals |
| `form_design` | React Hook Form + Zod forms with all 8 required UX states and blur-first validation |
| `animation` | Framer Motion animations — stagger, scroll-triggered, exit, parallax — GPU-only transforms |
| `responsive_layout` | Mobile-first layouts using `auto-fill + minmax`, `clamp()` typography, and container queries |
| `design_system` | Three-tier token architecture (primitive → semantic → component), 4px spacing scale, ThemeContext |
| `dark_mode` | Flash-free dark mode with CSS variables, `[data-theme]`, SSR blocking script, 3-option toggle |
| `auth_ui` | Branded auth flows (split-screen / full-bleed / dark-first) with Framer Motion step transitions |
| `state_management_react` | State taxonomy → Zustand slice pattern with selectors, Immer, and Context + useReducer |
| `accessibility_react` | WCAG 2.1 AA — semantic HTML, keyboard interaction, ARIA sparingly, jest-axe automated testing |

### Backend — 12 skills
| Skill | What it does |
|-------|-------------|
| `api_design` | Design RESTful endpoints: naming, verbs, status codes, pagination, idempotency |
| `caching_strategy` | Design cache topology, TTL policy, and event-based invalidation |
| `rate_limiting` | Design throttling: algorithm, tier structure, headers, and enforcement layer |
| `background_jobs` | Design worker architecture: queues, retries, DLQ, idempotency, observability |
| `error_handling` | Error taxonomy, propagation rules, logging contract, circuit breaker |
| `auth_backend` | Argon2 hashing, jose JWT, access + refresh token rotation, httpOnly cookies, RBAC middleware |
| `validation_node` | Zod `validate(schema, part)` middleware factory, `safeParse()`, `z.coerce` for query params |
| `caching_node` | Cache-aside `withCache<T>()`, Redis key naming `{env}:{resource}:{id}`, TTL strategy, single-flight |
| `logging_node` | Pino + AsyncLocalStorage request correlation, `getLogger()` child logger, redact config |
| `testing_backend_node` | Vitest + Supertest, feature-organized structure, unit (mock DB) vs integration (real test DB) |
| `database_schema` | Primary key selection, naming conventions, relationship patterns, composite index column order |
| `prisma_orm` | Prisma schema conventions, `select` over `include`, `$transaction`, N+1 prevention, migrations |

### Data — 6 skills
| Skill | What it does |
|-------|-------------|
| `data_model` | Design relational/document model: entities, indexes, constraints, migration path |
| `query_optimize` | Diagnose slow queries with EXPLAIN analysis and produce optimised rewrites |
| `etl_design` | Design ETL/ELT pipeline: idempotency, error handling, DLQ, scheduling |
| `data_quality` | Define quality rules (completeness, validity, freshness) and alerting thresholds |
| `ml_pipeline` | Design ML training and serving: data prep, evaluation gate, rollout, monitoring |
| `db_migration` | Generate safe reversible up/down schema migrations with risk flags |

### Mobile — 3 skills
| Skill | What it does |
|-------|-------------|
| `mobile_arch` | Architecture for iOS/Android/RN/Flutter: navigation, state, offline strategy |
| `offline_sync` | Offline-first sync design with conflict resolution and optimistic UI |
| `app_security` | OWASP Mobile Top 10 audit: storage, transport, auth, binary protections |

### DevOps — 5 skills
| Skill | What it does |
|-------|-------------|
| `dockerfile` | Production-ready multi-stage Dockerfile: non-root, pinned, minimal surface |
| `ci_design` | CI/CD pipeline: quality gates, environment promotion, secrets, rollback |
| `k8s_deploy` | Kubernetes manifests: Deployment, Service, HPA, PDB, NetworkPolicy |
| `infra_as_code` | Terraform module: resources, variables, outputs, state backend, tagging |
| `observability` | Observability stack: RED/USE metrics, structured logs, traces, alerting |

### Security — 4 skills
| Skill | What it does |
|-------|-------------|
| `security_audit` | OWASP Top 10 audit with file-and-line violations and concrete fixes |
| `threat_model` | STRIDE threat model: threats, risk ratings, and mitigations |
| `compliance_check` | GDPR / SOC 2 / HIPAA gap analysis with prioritised remediation list |
| `secret_management` | Secret storage, access control, rotation policy, and compromise playbook |

### Quality — 5 skills
| Skill | What it does |
|-------|-------------|
| `test_coverage` | Identify coverage gaps and generate missing tests (happy path + edge cases) |
| `explain` | Explain code in plain language — the WHY, not the WHAT |
| `debug` | Root-cause diagnosis with minimal fix — never suppress, never mask |
| `refactor` | Refactor for SOLID/clarity with zero behaviour change |
| `load_test` | Design load test scenarios: ramp profiles, SLOs, failure criteria, tool choice |

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
| `code_review` | 5-layer review hierarchy (correctness → security → performance → design → style) with blocking/suggestion/nit prefixes |
| `debugging` | 7-step root-cause process: reproduce → read error → narrow → hypothesise → verify → fix cause → verify fix |
| `refactoring` | Safety-net-first (characterization tests), commit at every green, high-churn files first |
| `technical_debt` | Fowler's debt quadrant, `Priority = Impact × Frequency × Risk`, DEBT.md, stakeholder framing in velocity terms |

### Next.js — 9 skills
| Skill | What it does |
|-------|-------------|
| `app_router` | App Router file conventions, route groups, parallel routes, intercepting routes |
| `server_components` | RSC vs Client Component decision rule, composition pattern, serialization boundary |
| `nextjs_middleware` | Edge Runtime constraints, JWT verification with `jose`, `matcher` config |
| `api_routes_nextjs` | Route Handler patterns, `NextRequest`/`NextResponse`, streaming responses |
| `nextjs_performance` | LCP image `priority`, `next/font`, dynamic imports >50 KB, `<Suspense>` at data boundaries |
| `typescript_patterns_nextjs` | Page props type, `useActionState` signature, discriminated unions, `satisfies` operator |
| `nextauth` | Auth.js v5 `auth()` unified API, `handlers` export, session TypeScript extension |
| `data_fetching_nextjs` | `fetch` cache options, `unstable_cache` for ORM data, `React.cache()` deduplication, `Promise.all` |
| `server_actions_nextjs` | `'use server'`, `useActionState`, return errors not throw, `useOptimistic`, `revalidateTag` |

### Flutter — 8 skills
| Skill | What it does |
|-------|-------------|
| `flutter_ui` | Const widgets, layout widget selection, `MediaQuery.sizeOf()`, Material 3 `ColorScheme.fromSeed` |
| `flutter_state` | Riverpod 2.0 provider types, `ref.watch/read/listen` rules, family providers, ProviderScope overrides |
| `flutter_navigation` | GoRouter with Riverpod (`@riverpod GoRouter`), named routes, `ShellRoute`, auth `redirect` guard |
| `flutter_networking` | Dio with `AuthInterceptor`, `@freezed` models, repository pattern, `DioException` mapping |
| `flutter_animations` | 3 animation layers, `TweenAnimationBuilder` cached child, `AnimationController` + dispose |
| `flutter_forms` | `GlobalKey<FormState>`, `TextEditingController` dispose, `AutovalidateMode.onUserInteraction` |
| `flutter_architecture` | Feature-first folder structure, 3-layer clean architecture, state ownership table |
| `flutter_testing` | `ProviderContainer` + tearDown, widget tests with `MockRepository`, pump sequence |

### Blazor — 8 skills
| Skill | What it does |
|-------|-------------|
| `blazor_components` | `EventCallback<T>`, `[EditorRequired]`, lifecycle method selection, `RenderFragment<T>`, `@key` |
| `blazor_forms` | `EditForm` + `OnValidSubmit`, DataAnnotations, FluentValidation, custom `InputBase<T>`, `EditContext` |
| `blazor_state` | 4-tier state approach — component fields / CascadingValue / scoped service / Fluxor |
| `blazor_auth` | `AuthenticationStateProvider`, `CascadingAuthenticationState`, `[Authorize]`, policy-based auth |
| `blazor_js_interop` | JS isolation modules (`.razor.js`), `IJSObjectReference` disposal, `DotNetObjectReference` |
| `blazor_data` | WASM typed `HttpClient` vs Blazor Server `IDbContextFactory<T>`, repository pattern |
| `blazor_routing` | `@page` constraints, `[SupplyParameterFromQuery]`, `NavigationManager`, `NavLink`, lazy loading |
| `blazor_performance` | `ShouldRender()` override, `Virtualize` component (fixed/variable/server-side), `@key` with record ID |

---

## Project Structure

```
multi-claude-agents/
├── agents/
│   ├── base.py              # BaseAgent: think() + act() + invoke_skill(); SV+Anthropic culture
│   ├── product_manager.py   # Writes PRD.md; reviews delivery against acceptance criteria
│   ├── architect.py         # Reads PRD; writes ARCHITECTURE.md + backlog_tasks.json
│   ├── coordinator.py       # Quality gate; suggest_approach() → skill/specialist/generalist
│   ├── developer.py         # Implements tasks; uses skill pre-processing output
│   ├── sdet.py              # pytest + bandit + ruff; translates AC into tests
│   ├── team_lead.py         # Loads backlog, assigns tasks, runs ceremonies
│   ├── safety_reviewer.py   # Constitutional review against 10-point Safety Constitution
│   └── __init__.py
├── skills/
│   ├── __init__.py          # Loads the full library on import
│   ├── registry.py          # Skill dataclass + SkillAgent + SkillRegistry
│   ├── catalog.py           # (legacy — superseded by library/)
│   └── library/
│       ├── __init__.py      # Imports all 16 category modules
│       ├── discovery.py     # decompose, tech_spike, user_story_map, problem_framing
│       ├── architecture.py  # system_design, adr, microservice_split, api_contract, capacity_plan
│       ├── frontend.py      # 14 skills — component_design, landing_page, form_design, animation, responsive_layout, design_system, dark_mode, auth_ui, state_management_react, accessibility_react, + 4 original audit skills
│       ├── backend.py       # 12 skills — api_design, auth_backend, validation_node, caching_node, caching_strategy, logging_node, testing_backend_node, database_schema, prisma_orm, rate_limiting, background_jobs, error_handling
│       ├── data.py          # data_model, query_optimize, etl_design, data_quality, ml_pipeline, db_migration
│       ├── mobile.py        # mobile_arch, offline_sync, app_security
│       ├── devops.py        # dockerfile, ci_design, k8s_deploy, infra_as_code, observability
│       ├── security.py      # security_audit, threat_model, compliance_check, secret_management
│       ├── quality.py       # test_coverage, explain, debug, refactor, load_test
│       ├── documentation.py # api_docs, changelog, readme_write, runbook
│       ├── integration.py   # webhook_design, messaging_design, payment_design, oauth_design
│       ├── realtime.py      # websocket_design, event_sourcing, stream_processing
│       ├── workflow.py      # git_workflow, pull_request, code_review, debugging, refactoring, technical_debt
│       ├── nextjs.py        # app_router, server_components, nextjs_middleware, api_routes_nextjs, nextjs_performance, typescript_patterns_nextjs, nextauth, data_fetching_nextjs, server_actions_nextjs
│       ├── flutter.py       # flutter_ui, flutter_state, flutter_navigation, flutter_networking, flutter_animations, flutter_forms, flutter_architecture, flutter_testing
│       └── blazor.py        # blazor_components, blazor_forms, blazor_state, blazor_auth, blazor_js_interop, blazor_data, blazor_routing, blazor_performance
├── tools/
│   ├── file_tools.py        # write_file, read_file, list_files, create_directory
│   ├── code_tools.py        # run_python, run_tests (pytest), run_bandit, run_ruff
│   ├── registry.py          # Tool schemas + dispatcher; role → tool mapping
│   └── __init__.py
├── team/
│   ├── team.py              # Team orchestrator: 7-step build pipeline + sprint simulation
│   ├── project.py           # ProjectSpec dataclass
│   ├── backlog.py           # Task dataclass + JSON-persisted Backlog
│   └── __init__.py
├── memory/
│   ├── decision_log.py      # Cross-project memory: records tech choices, rejections, outcomes
│   └── __init__.py
├── workspace/               # Created at runtime — one subdirectory per project
│   └── {project-name}/
│       ├── PRD.md           # Written by PM before architecture starts
│       ├── ARCHITECTURE.md
│       ├── backlog_tasks.json
│       └── <generated source + test files>
├── main.py                  # Entry point — --mode build|simulate
├── requirements.txt
└── .env.example
```

---

## Setup

**Requirements:** Python 3.11+

```bash
# 1. Clone
git clone <repo-url>
cd multi-claude-agents

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux

# Edit .env — set your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Usage

### Build a project (autonomous factory)

Edit `main.py` — change the `ProjectSpec` to describe whatever you want to build:

```python
spec = ProjectSpec(
    name="my-api",
    description="""
    Build a REST API for ...
    Features: ...
    """,
    tech_stack=["Python", "FastAPI", "SQLite", "pytest"],
)
```

Then run:

```bash
python main.py --mode build
```

The factory will:
1. **PM** writes `PRD.md` with user stories and acceptance criteria
2. **Architect** reads the PRD and writes `ARCHITECTURE.md` + `backlog_tasks.json`
3. **Eng Manager** loads and sequences the backlog
4. For each task: **Coordinator** routes it (generalist / skill assist / specialist), **Engineers** implement it, **Coordinator** quality-gates it with auto `security_audit` on sensitive tasks
5. **SDET** runs pytest, bandit, and ruff
6. **Safety Reviewer** runs a constitutional review of the full codebase
7. **PM** reviews the delivery against the acceptance criteria

Output example:
```json
{
  "project": "my-api",
  "workspace": "workspace/my-api",
  "sprints_run": 4,
  "files_created": ["main.py", "models/user.py", "routes/auth.py", "tests/test_auth.py"],
  "test_results": { "total_passed": 18, "total_failed": 0 },
  "skills_invoked": [
    { "task": "JWT auth endpoint", "skill": "security_audit", "triggered_by": "Sarah Kim" }
  ],
  "safety_review": { "constitutional": true, "findings": "CONSTITUTIONAL — all 10 principles satisfied" },
  "pm_delivery_review": "SHIPPED — all acceptance criteria met"
}
```

### Sprint simulation (no files written)

```bash
python main.py --mode simulate --sprints 3
```

Runs OKR-driven squad ceremonies (standup, code review, retrospective) with agents discussing work in natural language. Useful for exploring how agents collaborate.

---

## Using the Skills Library Directly

Any agent can invoke a skill mid-task:

```python
# Inside any agent method
result = self.invoke_skill("system_design", "Design a real-time chat system for 1M users")
result = self.invoke_skill("threat_model", "OAuth flow for a banking app")
result = self.invoke_skill("decompose", "Implement full-text search with ranking")
```

Standalone usage:

```python
from skills import SkillRegistry

# Invoke any skill by name
result = SkillRegistry.invoke("capacity_plan", "Social media feed for 10M DAU")

# List all skills
for skill in SkillRegistry.list_skills():
    print(f"[{skill.category}] {skill.name}: {skill.description}")

# Filter by category
data_skills = SkillRegistry.list_skills(category="data")
```

---

## Extending the System

### Add a new skill

Create or edit a file in `skills/library/` and call `SkillRegistry.register()`:

```python
from skills.registry import Skill, SkillRegistry

SkillRegistry.register(Skill(
    name="graphql_design",
    description="Design a GraphQL schema with types, queries, mutations, and subscriptions",
    category="backend",
    system_prompt="""You are a GraphQL API designer...""",
    tools=["read_file", "write_file"],  # tools from tools/registry.py TOOL_DEFINITIONS
))
```

Then import the file in `skills/library/__init__.py`.

### Add a new agent

1. Create `agents/my_agent.py` — extend `BaseAgent`, implement `_create_system_prompt()`
2. Add role-specific methods that call `self.think()`, `self.act()`, or `self.invoke_skill()`
3. Export from `agents/__init__.py`
4. Add to `Team.default()` in `team/team.py` and wire into `build_project()`

### Add a new tool

1. Implement the function in `tools/file_tools.py` or `tools/code_tools.py`
2. Add the Anthropic tool schema to `TOOL_DEFINITIONS` in `tools/registry.py`
3. Add a dispatch case in `execute_tool()`
4. Add the tool name to the relevant role(s) in `ROLE_TOOLS`

---

## Safety Constitution

The `SafetyReviewer` checks every codebase against these 10 non-negotiable principles before the PM's delivery review:

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

---

## Corporate Network (SSL / Proxy)

If you're on a network with SSL inspection (Zscaler, corporate proxy):

```bash
# Option A — bypass verification (quick, trusted networks only)
SSL_NO_VERIFY=true

# Option B — provide your corporate CA bundle (proper fix)
SSL_CERT_FILE=C:\path\to\corporate-ca.pem
```

---

## Key Design Decisions

**PM-first workflow** — The Product Manager writes `PRD.md` before the Architect touches the keyboard. The Architect reads the PRD before designing. This ensures the technical design is anchored to user outcomes, not just technical requirements.

**Skills as first-class citizens** — Skills are isolated Claude invocations with their own expert system prompts. They run in a clean context so they don't pollute the calling agent's conversation history. Any agent can invoke any skill without subclassing.

**Constitutional safety gate** — The Safety Reviewer is read-only by design (`read_file` + `list_files` only). It can never modify code, only report. Safety violations are logged to the DecisionLog and included in the build report. No other agent can override its verdict.

**Coordinator skill routing** — `suggest_approach()` shows the Coordinator the full skill catalogue and asks it to choose: generalist / skill / specialist. This means routing intelligence is itself an LLM call, not a hardcoded rule — the Coordinator can reason about which skill fits best.

**Prompt caching** — System prompts are marked `cache_control: ephemeral`. Claude caches them across the tool-use loop iterations, significantly reducing token costs for long tasks with many tool calls.

**Context reset per task** — Each `implement_task()` and `test_task()` call resets `self.messages = []`. Agents get a clean context per task rather than accumulating an ever-growing history.

**Atomic backlog writes** — `Backlog._save()` uses `os.replace()` for atomic JSON writes, preventing corruption on interruption.

**MAX_BUILD_SPRINTS = 10** — Guards against runaway loops. If the backlog isn't complete in 10 sprints, the factory stops and reports what was built.

---

## Model

All agents use `claude-sonnet-4-6` by default. Change `MODEL` in `agents/base.py` to use a different Claude model.

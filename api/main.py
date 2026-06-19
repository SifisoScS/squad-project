"""
Multi-Claude-Agents — FastAPI layer.

Endpoints:
  POST   /build                  kick off a build (auth required if API_SECRET_KEY set)
  DELETE /build/{id}             cancel a running build
  POST   /build/{id}/approve     approve a human-in-the-loop checkpoint (5.7)
  GET    /build/{id}/stream      SSE stream of agent output (reconnect-safe)
  GET    /build/{id}             current status + final report
  GET    /build/{id}/events      full event log as JSON
  GET    /build/{id}/trace       per-agent timing + token trace (5.5)
  GET    /builds                 paginated build list
  POST   /skill/invoke           invoke a single skill synchronously (4.3)
  GET    /skills                 list all registered skills
  GET    /skills/categories      skill category list
  GET    /workspaces             list generated project workspaces
  DELETE /workspace/{name}       delete a workspace
  GET    /health                 liveness probe
  GET    /                       Web UI

Run with:
  uvicorn api.main:app --reload --port 8000
"""

import asyncio
import builtins
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    _RATE_LIMIT_AVAILABLE = True
except ImportError:
    _RATE_LIMIT_AVAILABLE = False

import api.store as store
from api.auth import require_api_key
from api.models import BuildApproveRequest, BuildCreated, BuildInfo, BuildRequest, SkillInvokeRequest
from config import cfg
from team.project import ProjectSpec

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="Multi-Claude-Agents API", version="3.0.0")

# 2.8: CORS restricted to configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4.2: Rate limiting (gracefully absent if slowapi not installed)
if _RATE_LIMIT_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)


@app.on_event("startup")
async def _startup() -> None:
    """Initialise SQLite and reload persisted builds into memory."""
    store.init_db()
    for build in store.load_all():
        _builds[build["id"]] = build


# ── In-memory build store ─────────────────────────────────────────────────────
_builds: dict[str, dict] = {}
_running_teams: dict[str, object] = {}

# 1.1: Module-level asyncio.Lock for atomic concurrent build check-and-set
_build_lock: asyncio.Lock | None = None


def _get_build_lock() -> asyncio.Lock:
    global _build_lock
    if _build_lock is None:
        _build_lock = asyncio.Lock()
    return _build_lock


# 5.7: Checkpoint resume events, keyed by build_id
_checkpoint_events: dict[str, asyncio.Event] = {}

# ── Web UI ────────────────────────────────────────────────────────────────────

_UI_PATH = Path(__file__).parent / "static" / "index.html"


@app.get("/", include_in_schema=False)
async def serve_ui() -> HTMLResponse:
    return HTMLResponse(_UI_PATH.read_text(encoding="utf-8"))


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    import os
    running = sum(1 for b in _builds.values() if b["status"] == "running")
    return {
        "status": "ok",
        "builds_running": running,
        "builds_total": len(_builds),
        "api_key_configured": bool(os.environ.get("API_SECRET_KEY", "")),
    }


# ── Builds ────────────────────────────────────────────────────────────────────

@app.get("/builds")
async def list_builds(
    page: int = 1,
    page_size: int = 25,
    status: str | None = None,
):
    """Paginated build list (4.4). Returns most recent first."""
    all_builds = list(reversed(list(_builds.values())))
    if status:
        all_builds = [b for b in all_builds if b["status"] == status]
    total = len(all_builds)
    page_size = min(max(1, page_size), 100)
    start = (max(1, page) - 1) * page_size
    page_builds = all_builds[start : start + page_size]
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "builds": [
            {
                "id": b["id"],
                "status": b["status"],
                "spec_name": b["spec_name"],
                "events_count": len(b.get("events", [])),
                "created_at": b.get("created_at", ""),
            }
            for b in page_builds
        ],
    }


@app.post("/build", response_model=BuildCreated, status_code=202)
async def start_build(
    request: Request,
    req: BuildRequest,
    _auth=Depends(require_api_key),  # 1.5: auth on mutating route
):
    # 1.1: Async lock prevents two simultaneous start_build() calls from both
    # passing the "is anything running?" check.
    async with _get_build_lock():
        if any(b["status"] == "running" for b in _builds.values()):
            raise HTTPException(409, detail="A build is already in progress — wait for it to complete.")

        build_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        _builds[build_id] = {
            "id": build_id,
            "status": "running",
            "spec_name": req.name,
            "events": [],
            "result": {},
            "created_at": created_at,
            "trace": [],
        }

    spec = ProjectSpec(
        name=req.name,
        description=req.description,
        tech_stack=req.tech_stack,
        build_timeout_seconds=req.build_timeout_seconds,
        human_checkpoints=req.human_checkpoints,
    )
    asyncio.create_task(_run_build(build_id, spec))
    return BuildCreated(id=build_id)


@app.delete("/build/{build_id}", tags=["builds"])
async def cancel_build(
    build_id: str,
    _auth=Depends(require_api_key),
):
    b = _require_build(build_id)
    if b["status"] not in ("running", "awaiting_review"):
        raise HTTPException(409, detail=f"Build is not active (status: {b['status']})")
    team = _running_teams.get(build_id)
    if team:
        team.cancel()
    b["status"] = "cancelled"
    b["events"].append("[Squad] Build cancelled by API request")
    # Unblock any waiting checkpoint
    evt = _checkpoint_events.pop(build_id, None)
    if evt:
        evt.set()
    return {"id": build_id, "status": "cancelled"}


@app.post("/build/{build_id}/approve", tags=["builds"])
async def approve_checkpoint(
    build_id: str,
    req: BuildApproveRequest,
    _auth=Depends(require_api_key),
):
    """Resume a build that is awaiting a human-in-the-loop checkpoint (5.7)."""
    b = _require_build(build_id)
    if b["status"] != "awaiting_review":
        raise HTTPException(409, detail=f"Build is not awaiting review (status: {b['status']})")
    b["status"] = "running"
    b["events"].append(f"[Squad] Checkpoint '{req.checkpoint}' approved. Resuming build.")
    evt = _checkpoint_events.get(build_id)
    if evt:
        evt.set()
    return {"id": build_id, "status": "running", "checkpoint": req.checkpoint}


@app.get("/build/{build_id}", response_model=BuildInfo)
async def get_build(build_id: str):
    b = _require_build(build_id)
    return BuildInfo(
        id=b["id"],
        status=b["status"],
        spec_name=b["spec_name"],
        events_count=len(b["events"]),
        result=b["result"],
    )


@app.get("/build/{build_id}/events")
async def get_events(build_id: str):
    b = _require_build(build_id)
    return {"id": build_id, "status": b["status"], "events": b["events"]}


@app.get("/build/{build_id}/trace")
async def get_trace(build_id: str):
    """Per-agent timing and token trace (5.5)."""
    b = _require_build(build_id)
    return {"id": build_id, "trace": b.get("trace", [])}


@app.get("/build/{build_id}/stream")
async def stream_build(build_id: str):
    b = _require_build(build_id)
    return StreamingResponse(
        _event_generator(b),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Skills ────────────────────────────────────────────────────────────────────

@app.post("/skill/invoke")
async def invoke_skill(
    req: SkillInvokeRequest,
    _auth=Depends(require_api_key),
):
    """Invoke a single skill synchronously and return its output (4.3)."""
    import skills as _s  # noqa — ensures all skills are registered
    from skills.registry import SkillRegistry
    try:
        loop = asyncio.get_running_loop()
        output = await loop.run_in_executor(
            None, SkillRegistry.invoke, req.skill_name, req.task
        )
        return {"skill": req.skill_name, "output": output}
    except KeyError as e:
        raise HTTPException(404, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"Skill invocation failed: {e}")


@app.get("/skills")
async def list_skills(category: str | None = None):
    import skills as _skills_module  # noqa
    from skills.registry import SkillRegistry
    skill_list = SkillRegistry.list_skills(category=category)
    return [
        {"name": s.name, "description": s.description, "category": s.category}
        for s in skill_list
    ]


@app.get("/skills/categories")
async def list_skill_categories():
    import skills as _skills_module  # noqa
    from skills.registry import SkillRegistry
    categories = sorted({s.category for s in SkillRegistry.list_skills()})
    return categories


# ── Workspaces ────────────────────────────────────────────────────────────────

@app.get("/workspaces")
async def list_workspaces():
    ws_root = Path(cfg.WORKSPACE_ROOT)
    if not ws_root.exists():
        return []
    return sorted(
        [
            {
                "name": d.name,
                "path": str(d),
                "file_count": sum(1 for _ in d.rglob("*") if _.is_file()),
            }
            for d in ws_root.iterdir()
            if d.is_dir()
        ],
        key=lambda x: x["name"],
    )


@app.delete("/workspace/{name}")
async def delete_workspace(
    name: str,
    _auth=Depends(require_api_key),
):
    if "/" in name or "\\" in name or ".." in name:
        raise HTTPException(400, detail="Invalid workspace name")
    ws_path = Path(cfg.WORKSPACE_ROOT) / name
    if not ws_path.exists():
        raise HTTPException(404, detail=f"Workspace '{name}' not found")
    shutil.rmtree(ws_path)
    return {"deleted": name}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_build(build_id: str) -> dict:
    b = _builds.get(build_id)
    if not b:
        raise HTTPException(404, detail="Build not found")
    return b


async def _event_generator(build: dict) -> AsyncIterator[str]:
    """SSE generator — replays existing events first, then tails live output."""
    idx = 0
    while True:
        events = build["events"]
        while idx < len(events):
            line = events[idx].replace("\r", "").replace("\n", " | ")
            yield f"data: {line}\n\n"
            idx += 1

        status = build["status"]
        if status not in ("running", "awaiting_review"):
            yield f"event: done\ndata: {status}\n\n"
            break

        if status == "awaiting_review":
            yield f"event: checkpoint\ndata: awaiting_review\n\n"

        await asyncio.sleep(0.05)


async def _run_build(build_id: str, spec: ProjectSpec) -> None:
    """Async wrapper — hands blocking work to the thread-pool executor."""
    build = _builds[build_id]
    loop = asyncio.get_running_loop()

    def on_line(line: str) -> None:
        build["events"].append(line)

    # 5.7: Checkpoint callback — pauses the build for human review
    async def on_checkpoint(checkpoint_name: str) -> None:
        build["status"] = "awaiting_review"
        build["events"].append(f"[Squad] Checkpoint reached: {checkpoint_name} — awaiting human approval")
        evt = asyncio.Event()
        _checkpoint_events[build_id] = evt
        await evt.wait()
        _checkpoint_events.pop(build_id, None)

    try:
        # 2.3: Build timeout
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None, _sync_build, build_id, spec, on_line, loop, on_checkpoint
            ),
            timeout=spec.build_timeout_seconds,
        )
        build["result"] = result
        build["status"] = "completed"
    except asyncio.TimeoutError:
        build["status"] = "timeout"
        build["result"] = {"error": f"Build timed out after {spec.build_timeout_seconds}s"}
        build["events"].append(f"[FATAL] Build timed out after {spec.build_timeout_seconds}s")
    except Exception as exc:
        build["status"] = "failed"
        build["result"] = {"error": str(exc)}
        build["events"].append(f"[FATAL] {exc}")
    finally:
        _running_teams.pop(build_id, None)
        store.save(build)


def _sync_build(build_id: str, spec: ProjectSpec, on_line, loop, on_checkpoint) -> dict:
    """Blocking build — runs inside run_in_executor."""
    from team import Team

    _orig_print = builtins.print

    def _patched(*args, sep=" ", end="\n", file=None, flush=False):
        _orig_print(*args, sep=sep, end=end, file=file, flush=flush)
        if file is None or file is sys.stdout:
            on_line(sep.join(str(a) for a in args))

    builtins.print = _patched
    try:
        team = Team.default()
        _running_teams[build_id] = team

        # Wrap async checkpoint callback for the synchronous build thread
        def sync_checkpoint(name: str) -> None:
            future = asyncio.run_coroutine_threadsafe(on_checkpoint(name), loop)
            future.result()  # block thread until checkpoint approved

        return team.build_project(spec, checkpoint_callback=sync_checkpoint)
    finally:
        builtins.print = _orig_print

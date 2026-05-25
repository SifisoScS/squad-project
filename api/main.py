"""
Multi-Claude-Agents — FastAPI layer.

Endpoints:
  POST   /build                  kick off a build, returns build_id immediately
  DELETE /build/{id}             cancel a running build (#8)
  GET    /build/{id}/stream      SSE stream of agent output (reconnect-safe)
  GET    /build/{id}             current status + final report
  GET    /build/{id}/events      full event log as JSON
  GET    /builds                 list all builds (most recent first)
  GET    /skills                 list all registered skills (#5)
  GET    /workspaces             list generated project workspaces (#5)
  DELETE /workspace/{name}       delete a workspace (#5)
  GET    /health                 liveness probe
  GET    /                       Web UI (#1)

Run with:
  uvicorn api.main:app --reload --port 8000
"""

import asyncio
import builtins
import shutil
import sys
import uuid
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

import api.store as store
from api.models import BuildCreated, BuildInfo, BuildRequest
from team.project import ProjectSpec

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="Multi-Claude-Agents API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup() -> None:
    """Initialise SQLite and reload persisted builds into memory (#3)."""
    store.init_db()
    for build in store.load_all():
        _builds[build["id"]] = build


# ── In-memory build store ─────────────────────────────────────────────────────
# Live event lists for active builds. Completed builds are persisted to SQLite
# by store.save() and reloaded here on the next server start.
_builds: dict[str, dict] = {}

# Running Team instances, keyed by build_id — needed for cancellation (#8)
_running_teams: dict[str, object] = {}

# ── Web UI (#1) ───────────────────────────────────────────────────────────────

_UI_PATH = Path(__file__).parent / "static" / "index.html"


@app.get("/", include_in_schema=False)
async def serve_ui() -> HTMLResponse:
    return HTMLResponse(_UI_PATH.read_text(encoding="utf-8"))


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    running = sum(1 for b in _builds.values() if b["status"] == "running")
    return {"status": "ok", "builds_running": running, "builds_total": len(_builds)}


@app.get("/builds")
async def list_builds():
    return [
        {
            "id": b["id"],
            "status": b["status"],
            "spec_name": b["spec_name"],
            "events_count": len(b["events"]),
        }
        for b in reversed(list(_builds.values()))
    ]


@app.post("/build", response_model=BuildCreated, status_code=202)
async def start_build(req: BuildRequest):
    if any(b["status"] == "running" for b in _builds.values()):
        raise HTTPException(409, detail="A build is already in progress — wait for it to complete.")

    build_id = str(uuid.uuid4())
    _builds[build_id] = {
        "id": build_id,
        "status": "running",
        "spec_name": req.name,
        "events": [],
        "result": {},
    }

    spec = ProjectSpec(name=req.name, description=req.description, tech_stack=req.tech_stack)
    asyncio.create_task(_run_build(build_id, spec))
    return BuildCreated(id=build_id)


@app.delete("/build/{build_id}", tags=["builds"])
async def cancel_build(build_id: str):
    """
    Cancel a running build (#8).
    Sets the cancellation flag on the Team — the build stops cleanly after
    the current task completes (mid-task work is not interrupted).
    """
    b = _require_build(build_id)
    if b["status"] != "running":
        raise HTTPException(409, detail=f"Build is not running (status: {b['status']})")
    team = _running_teams.get(build_id)
    if team:
        team.cancel()
    b["status"] = "cancelled"
    b["events"].append("[Squad] Build cancelled by API request")
    return {"id": build_id, "status": "cancelled"}


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


@app.get("/build/{build_id}/stream")
async def stream_build(build_id: str):
    b = _require_build(build_id)
    return StreamingResponse(
        _event_generator(b),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Skills endpoint (#5) ──────────────────────────────────────────────────────

@app.get("/skills")
async def list_skills(category: str | None = None):
    """
    List all registered skills, optionally filtered by category.
    Imports the full skill library lazily so the endpoint is always up-to-date.
    """
    import skills as _skills_module  # noqa — ensures all skills are registered
    from skills.registry import SkillRegistry
    skill_list = SkillRegistry.list_skills(category=category)
    return [
        {"name": s.name, "description": s.description, "category": s.category}
        for s in skill_list
    ]


@app.get("/skills/categories")
async def list_skill_categories():
    """Return the distinct skill categories available."""
    import skills as _skills_module  # noqa
    from skills.registry import SkillRegistry
    categories = sorted({s.category for s in SkillRegistry.list_skills()})
    return categories


# ── Workspaces endpoints (#5) ─────────────────────────────────────────────────

@app.get("/workspaces")
async def list_workspaces():
    """List all generated project workspaces under workspace/."""
    ws_root = Path("workspace")
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
async def delete_workspace(name: str):
    """Delete a generated project workspace by name."""
    # Prevent path traversal
    if "/" in name or "\\" in name or ".." in name:
        raise HTTPException(400, detail="Invalid workspace name")
    ws_path = Path("workspace") / name
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
    """
    SSE generator — replays existing events first, then tails live output.
    Reconnect-safe: restarts from idx=0 each time (events list is append-only).
    """
    idx = 0
    while True:
        events = build["events"]
        while idx < len(events):
            line = events[idx].replace("\r", "").replace("\n", " | ")
            yield f"data: {line}\n\n"
            idx += 1

        if build["status"] != "running":
            yield f"event: done\ndata: {build['status']}\n\n"
            break

        await asyncio.sleep(0.05)


async def _run_build(build_id: str, spec: ProjectSpec) -> None:
    """Async wrapper — hands blocking work to the thread-pool executor."""
    build = _builds[build_id]
    loop = asyncio.get_running_loop()

    def on_line(line: str) -> None:
        build["events"].append(line)

    try:
        result = await loop.run_in_executor(None, _sync_build, build_id, spec, on_line)
        build["result"] = result
        build["status"] = "completed"
    except Exception as exc:
        build["status"] = "failed"
        build["result"] = {"error": str(exc)}
        build["events"].append(f"[FATAL] {exc}")
    finally:
        _running_teams.pop(build_id, None)
        store.save(build)  # persist to SQLite (#3)


def _sync_build(build_id: str, spec: ProjectSpec, on_line) -> dict:
    """
    Blocking build — runs inside run_in_executor.

    Patches builtins.print so every agent print() call is forwarded to the
    event log AND original stdout. The 409 guard on POST /build ensures only
    one build runs at a time, keeping this process-global patch safe.
    """
    from team import Team

    _orig_print = builtins.print

    def _patched(*args, sep=" ", end="\n", file=None, flush=False):
        _orig_print(*args, sep=sep, end=end, file=file, flush=flush)
        if file is None or file is sys.stdout:
            on_line(sep.join(str(a) for a in args))

    builtins.print = _patched
    try:
        team = Team.default()
        _running_teams[build_id] = team   # register for cancellation (#8)
        return team.build_project(spec)
    finally:
        builtins.print = _orig_print

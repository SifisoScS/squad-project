"""
Multi-Claude-Agents — FastAPI streaming layer.

Endpoints:
  POST /build                 kick off a build, returns build_id immediately
  GET  /build/{id}/stream     SSE stream of agent print output (reconnect-safe)
  GET  /build/{id}            current status + final report once complete
  GET  /build/{id}/events     full event log as JSON (for replay / debugging)
  GET  /builds                list all builds (most recent first)
  GET  /health                liveness probe

Run with:
  uvicorn api.main:app --reload --port 8000
"""

import asyncio
import builtins
import sys
import uuid
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from api.models import BuildCreated, BuildInfo, BuildRequest
from team.project import ProjectSpec

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="Multi-Claude-Agents API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory build store ─────────────────────────────────────────────────────
# Each entry: {id, status, spec_name, events: list[str], result: dict}
_builds: dict[str, dict] = {}


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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_build(build_id: str) -> dict:
    b = _builds.get(build_id)
    if not b:
        raise HTTPException(404, detail="Build not found")
    return b


async def _event_generator(build: dict) -> AsyncIterator[str]:
    """
    SSE generator — replays existing events first, then tails live output.
    Safe to reconnect: start from index 0 each time and poll the shared list.
    """
    idx = 0
    while True:
        events = build["events"]
        while idx < len(events):
            # Escape newlines so one SSE data line = one agent print line
            line = events[idx].replace("\r", "").replace("\n", " | ")
            yield f"data: {line}\n\n"
            idx += 1

        if build["status"] != "running":
            yield f"event: done\ndata: {build['status']}\n\n"
            break

        await asyncio.sleep(0.05)


async def _run_build(build_id: str, spec: ProjectSpec) -> None:
    """Async wrapper — hands off blocking work to a thread pool executor."""
    build = _builds[build_id]
    loop = asyncio.get_running_loop()

    def on_line(line: str) -> None:
        build["events"].append(line)

    try:
        result = await loop.run_in_executor(None, _sync_build, spec, on_line)
        build["result"] = result
        build["status"] = "completed"
    except Exception as exc:
        build["status"] = "failed"
        build["result"] = {"error": str(exc)}
        build["events"].append(f"[FATAL] {exc}")


def _sync_build(spec: ProjectSpec, on_line) -> dict:
    """
    Blocking build that runs inside run_in_executor.

    Patches builtins.print for the duration so every agent print() call is
    both forwarded to the original stdout AND appended to the event log.

    Note: this patch is process-global. Concurrent builds are blocked at the
    /build endpoint (409 if one is already running) to keep the patch safe.
    """
    _orig_print = builtins.print

    def _patched(*args, sep=" ", end="\n", file=None, flush=False):
        _orig_print(*args, sep=sep, end=end, file=file, flush=flush)
        if file is None or file is sys.stdout:
            on_line(sep.join(str(a) for a in args))

    builtins.print = _patched
    try:
        from team import Team  # imported here to avoid circular imports at module load
        team = Team.default()
        return team.build_project(spec)
    finally:
        builtins.print = _orig_print

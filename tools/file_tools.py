import os
import threading
from pathlib import Path

# Per-file write locks (1.2): prevents concurrent developers from silently
# overwriting each other's work when building in parallel.
_file_locks: dict[str, threading.Lock] = {}
_locks_registry_lock = threading.Lock()


def _get_file_lock(resolved_path: str) -> threading.Lock:
    with _locks_registry_lock:
        if resolved_path not in _file_locks:
            _file_locks[resolved_path] = threading.Lock()
        return _file_locks[resolved_path]


def _safe_path(path: str, workspace_root: Path) -> Path:
    resolved_root = workspace_root.resolve()
    resolved_target = (workspace_root / path).resolve()
    if not resolved_target.is_relative_to(resolved_root):
        raise ValueError(f"Path '{path}' escapes workspace root")
    return resolved_target


def write_file(path: str, content: str, workspace_root: Path) -> dict:
    try:
        target = _safe_path(path, workspace_root)
        file_lock = _get_file_lock(str(target))
        with file_lock:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return {"success": True, "path": str(target.relative_to(workspace_root)), "bytes_written": len(content.encode())}
    except ValueError as e:
        return {"error": str(e)}
    except OSError as e:
        return {"error": f"File write failed: {e}"}


def read_file(path: str, workspace_root: Path) -> dict:
    try:
        target = _safe_path(path, workspace_root)
        if not target.exists():
            return {"error": f"File not found: {path}"}
        content = target.read_text(encoding="utf-8")
        return {"success": True, "path": path, "content": content}
    except ValueError as e:
        return {"error": str(e)}
    except OSError as e:
        return {"error": f"File read failed: {e}"}


def list_files(directory: str, workspace_root: Path) -> dict:
    try:
        target = _safe_path(directory, workspace_root)
        if not target.exists():
            return {"error": f"Directory not found: {directory}"}
        files = []
        for p in sorted(target.rglob("*")):
            if p.is_file():
                try:
                    rel = str(p.relative_to(workspace_root))
                    files.append({"path": rel, "size": p.stat().st_size})
                except (ValueError, OSError):
                    pass
        return {"success": True, "files": files}
    except ValueError as e:
        return {"error": str(e)}
    except OSError as e:
        return {"error": f"List failed: {e}"}


def create_directory(path: str, workspace_root: Path) -> dict:
    try:
        target = _safe_path(path, workspace_root)
        target.mkdir(parents=True, exist_ok=True)
        return {"success": True, "path": str(target.relative_to(workspace_root))}
    except ValueError as e:
        return {"error": str(e)}
    except OSError as e:
        return {"error": f"Directory creation failed: {e}"}

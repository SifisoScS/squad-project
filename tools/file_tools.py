import os
from pathlib import Path


def _safe_path(path: str, workspace_root: Path) -> Path:
    resolved_root = workspace_root.resolve()
    resolved_target = (workspace_root / path).resolve()
    if not resolved_target.is_relative_to(resolved_root):
        raise ValueError(f"Path '{path}' escapes workspace root")
    return resolved_target


def write_file(path: str, content: str, workspace_root: Path) -> dict:
    try:
        target = _safe_path(path, workspace_root)
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

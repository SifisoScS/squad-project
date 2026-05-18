import re
import sys
import subprocess
from pathlib import Path


def run_bandit(target_path: str, workspace_root: Path) -> dict:
    """Run bandit security scanner on Python files. Gracefully skips if not installed."""
    from tools.file_tools import _safe_path
    try:
        target = _safe_path(target_path, workspace_root)
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "-r", str(target), "-f", "txt"],
            capture_output=True, text=True, timeout=60, cwd=str(workspace_root),
        )
        output = result.stdout + result.stderr
        if "No module named bandit" in output:
            return {"skipped": True, "reason": "bandit not installed — add bandit to requirements.txt"}
        issues = len(re.findall(r">> Issue:", result.stdout))
        return {
            "success": True,
            "issues_found": issues,
            "output": result.stdout[:3000],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": "bandit timed out after 60s"}
    except Exception as e:
        return {"error": str(e)}


def run_ruff(target_path: str, workspace_root: Path) -> dict:
    """Run ruff linter on Python files for code quality issues. Gracefully skips if not installed."""
    from tools.file_tools import _safe_path
    try:
        target = _safe_path(target_path, workspace_root)
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(target)],
            capture_output=True, text=True, timeout=30, cwd=str(workspace_root),
        )
        output = result.stdout + result.stderr
        if "No module named ruff" in output:
            return {"skipped": True, "reason": "ruff not installed — add ruff to requirements.txt"}
        violation_lines = [
            ln for ln in result.stdout.splitlines()
            if ln and not ln.startswith("Found") and not ln.startswith("All checks")
        ]
        return {
            "success": result.returncode == 0,
            "violations": len(violation_lines),
            "output": result.stdout[:3000],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": "ruff timed out after 30s"}
    except Exception as e:
        return {"error": str(e)}


def run_python(script_path: str, args: list, workspace_root: Path) -> dict:
    from tools.file_tools import _safe_path
    try:
        target = _safe_path(script_path, workspace_root)
        if not target.exists():
            return {"error": f"Script not found: {script_path}", "stdout": "", "stderr": ""}
        cmd = [sys.executable, str(target)] + [str(a) for a in (args or [])]
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=30, cwd=str(workspace_root)
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Script timed out after 30s", "stdout": "", "stderr": ""}
    except Exception as e:
        return {"error": str(e), "stdout": "", "stderr": ""}


def run_tests(test_path: str, workspace_root: Path) -> dict:
    from tools.file_tools import _safe_path
    try:
        target = _safe_path(test_path, workspace_root)
        cmd = [sys.executable, "-m", "pytest", str(target), "-v", "--tb=short"]
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=120, cwd=str(workspace_root)
        )
        output = result.stdout + result.stderr

        # pytest not installed
        if "No module named pytest" in output:
            return {"error": "pytest not installed — add pytest to requirements.txt", "output": output}

        # returncode 4 = no tests collected
        if result.returncode == 4:
            return {"success": True, "passed": 0, "failed": 0, "errors": 1,
                    "output": output, "note": "No tests collected"}

        passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", output)) else 0
        failed = int(m.group(1)) if (m := re.search(r"(\d+) failed", output)) else 0
        errors = int(m.group(1)) if (m := re.search(r"(\d+) error", output)) else 0

        return {
            "success": failed == 0 and errors == 0,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "output": output,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Tests timed out after 120s", "output": ""}
    except Exception as e:
        return {"error": str(e), "output": ""}

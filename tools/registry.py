import json
from pathlib import Path

_workspace_root: Path | None = None


def set_workspace(path: Path) -> None:
    global _workspace_root
    _workspace_root = path


TOOL_DEFINITIONS: dict[str, dict] = {
    "write_file": {
        "name": "write_file",
        "description": (
            "Write content to a file in the project workspace. "
            "Creates parent directories automatically. "
            "Use relative paths from the workspace root (e.g. 'src/models/user.py')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative file path from workspace root"},
                "content": {"type": "string", "description": "Full file content to write"},
            },
            "required": ["path", "content"],
        },
    },
    "read_file": {
        "name": "read_file",
        "description": (
            "Read the content of a file in the project workspace. "
            "Use relative paths from the workspace root."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative file path from workspace root"},
            },
            "required": ["path"],
        },
    },
    "list_files": {
        "name": "list_files",
        "description": (
            "List all files recursively in a directory of the project workspace. "
            "Returns file paths and sizes. Use '.' for the workspace root."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Relative directory path, e.g. 'src' or '.'"},
            },
            "required": ["directory"],
        },
    },
    "create_directory": {
        "name": "create_directory",
        "description": (
            "Create a directory (and all parent directories) in the project workspace. "
            "Idempotent — safe to call even if the directory already exists."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative directory path from workspace root"},
            },
            "required": ["path"],
        },
    },
    "run_python": {
        "name": "run_python",
        "description": (
            "Run a Python script in the project workspace. "
            "Captures stdout and stderr. 30-second timeout. "
            "Use for verifying syntax or running quick checks. "
            "Use run_tests for the test suite."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "script_path": {"type": "string", "description": "Relative path to the Python script"},
                "args": {"type": "array", "items": {"type": "string"}, "description": "CLI arguments", "default": []},
            },
            "required": ["script_path"],
        },
    },
    "run_tests": {
        "name": "run_tests",
        "description": (
            "Run pytest on a test file or directory in the project workspace. "
            "Returns pass/fail counts and full pytest output."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "test_path": {"type": "string", "description": "Relative path to test file or directory, e.g. 'tests/'"},
            },
            "required": ["test_path"],
        },
    },
    "run_bandit": {
        "name": "run_bandit",
        "description": (
            "Run bandit security scanner on Python files. "
            "Returns the count of security issues found and their descriptions. "
            "Skips gracefully if bandit is not installed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target_path": {"type": "string", "description": "Relative path to file or directory to scan"},
            },
            "required": ["target_path"],
        },
    },
    "run_ruff": {
        "name": "run_ruff",
        "description": (
            "Run ruff linter on Python files for code quality and style violations. "
            "Returns violation count and details. "
            "Skips gracefully if ruff is not installed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target_path": {"type": "string", "description": "Relative path to file or directory to lint"},
            },
            "required": ["target_path"],
        },
    },
}

ROLE_TOOLS: dict[str, list[str]] = {
    "architect":        ["write_file", "read_file", "create_directory"],
    "developer":        ["read_file", "write_file", "create_directory", "run_python"],
    "sdet":             ["read_file", "write_file", "run_tests", "run_bandit", "run_ruff"],
    "team_lead":        ["read_file", "write_file", "list_files"],
    "coordinator":      ["read_file", "list_files"],
    "product_manager":  ["write_file", "read_file", "list_files"],
    "safety_reviewer":  ["read_file", "list_files"],  # read-only by design — never modifies the codebase
}


def get_tools_for_role(role: str) -> list[dict]:
    names = ROLE_TOOLS.get(role, [])
    return [TOOL_DEFINITIONS[n] for n in names]


def execute_tool(name: str, input_data: dict) -> str:
    if _workspace_root is None:
        return json.dumps({"error": "Workspace not set — call set_workspace() before running agents"})
    try:
        from tools.file_tools import write_file, read_file, list_files, create_directory
        from tools.code_tools import run_python, run_tests, run_bandit, run_ruff

        if name == "write_file":
            result = write_file(input_data["path"], input_data["content"], _workspace_root)
        elif name == "read_file":
            result = read_file(input_data["path"], _workspace_root)
        elif name == "list_files":
            result = list_files(input_data.get("directory", "."), _workspace_root)
        elif name == "create_directory":
            result = create_directory(input_data["path"], _workspace_root)
        elif name == "run_python":
            result = run_python(input_data["script_path"], input_data.get("args", []), _workspace_root)
        elif name == "run_tests":
            result = run_tests(input_data["test_path"], _workspace_root)
        elif name == "run_bandit":
            result = run_bandit(input_data["target_path"], _workspace_root)
        elif name == "run_ruff":
            result = run_ruff(input_data["target_path"], _workspace_root)
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as e:
        result = {"error": f"Tool execution failed: {e}"}

    return json.dumps(result)

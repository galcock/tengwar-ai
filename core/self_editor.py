"""
Tengwar AI — Self-Editor
Gives the AI the ability to read and modify its own files,
the Tengwar language source, and the tengwar.ai website.
This is how it improves itself.
"""
import os
import subprocess
from pathlib import Path
from . import memory

# Root directories the AI can access
AI_ROOT = Path(__file__).parent.parent  # tengwar-ai/
TENGWAR_ROOT = AI_ROOT.parent / "tengwar-lang"  # ../tengwar-lang/
ALLOWED_ROOTS = [AI_ROOT, TENGWAR_ROOT]


def _is_safe_path(path: str) -> bool:
    """Ensure path is within allowed directories."""
    p = Path(path).resolve()
    return any(str(p).startswith(str(root.resolve())) for root in ALLOWED_ROOTS)


def read_file(path: str) -> str:
    if not _is_safe_path(path):
        return f"[Error: Access denied — path outside allowed directories]"
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return f"[Error reading {path}: {e}]"


def write_file(path: str, content: str) -> str:
    if not _is_safe_path(path):
        return f"[Error: Access denied — path outside allowed directories]"
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
        memory.store_memory(
            type="self_edit",
            content=f"Modified file: {path}",
            importance=0.8,
            metadata={"file": path, "size": len(content)}
        )
        return f"[Written {len(content)} bytes to {path}]"
    except Exception as e:
        return f"[Error writing {path}: {e}]"


def list_dir(path: str) -> list:
    if not _is_safe_path(path):
        return ["[Error: Access denied]"]
    try:
        p = Path(path)
        items = []
        for item in sorted(p.iterdir()):
            if item.name.startswith('.') or item.name == '__pycache__' or item.name == 'node_modules':
                continue
            prefix = "📁 " if item.is_dir() else "📄 "
            items.append(prefix + item.name)
        return items
    except Exception as e:
        return [f"[Error: {e}]"]


def git_status() -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(TENGWAR_ROOT),
            capture_output=True, text=True, timeout=10
        )
        return result.stdout or "(clean)"
    except Exception as e:
        return f"[Git error: {e}]"


def git_commit(message: str) -> str:
    try:
        subprocess.run(["git", "add", "-A"], cwd=str(TENGWAR_ROOT),
                       capture_output=True, timeout=10)
        result = subprocess.run(
            ["git", "commit", "-m", f"[Tengwar AI] {message}"],
            cwd=str(TENGWAR_ROOT),
            capture_output=True, text=True, timeout=10
        )
        memory.store_memory(
            type="self_edit",
            content=f"Git commit: {message}",
            importance=0.9,
            metadata={"output": result.stdout[:500]}
        )
        return result.stdout or result.stderr
    except Exception as e:
        return f"[Git error: {e}]"


def get_available_tools() -> dict:
    """Return tool descriptions for the LLM to understand its capabilities."""
    return {
        "read_file": "Read a file's contents. Args: path (string)",
        "write_file": "Write content to a file. Args: path (string), content (string)",
        "list_dir": "List directory contents. Args: path (string)",
        "git_status": "Check git status of the Tengwar repo",
        "git_commit": "Commit changes with a message. Args: message (string)",
    }

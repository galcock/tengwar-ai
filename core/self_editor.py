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

# Root directories the AI can access — these are the actual paths on Gary's MacBook
AI_ROOT = Path.home() / "tengwar-ai"
TENGWAR_ROOT = Path.home() / "tengwar"
ALLOWED_ROOTS = [AI_ROOT, TENGWAR_ROOT]


def _is_safe_path(path: str) -> bool:
    """Ensure path is within allowed directories."""
    p = Path(path).resolve()
    return any(str(p).startswith(str(root.resolve())) for root in ALLOWED_ROOTS if root.exists())


def read_file(path: str) -> str:
    if not _is_safe_path(path):
        return f"[Error: Access denied — path '{path}' is outside allowed directories ({', '.join(str(r) for r in ALLOWED_ROOTS)})]"
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return f"[Error reading {path}: {e}]"


def write_file(path: str, content: str) -> str:
    if not _is_safe_path(path):
        return f"[Error: Access denied — path '{path}' is outside allowed directories]"
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
        memory.store_memory(
            type="self_edit",
            content=f"Modified file: {path} ({len(content)} bytes)",
            importance=0.8,
            metadata={"file": path, "size": len(content)}
        )
        return f"Written {len(content)} bytes to {path}"
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
            size = ""
            if item.is_file():
                s = item.stat().st_size
                size = f" ({s:,} bytes)" if s < 100000 else f" ({s//1024}KB)"
            items.append(prefix + item.name + size)
        return items
    except Exception as e:
        return [f"[Error: {e}]"]


def git_status(repo: str = None) -> str:
    cwd = repo or str(TENGWAR_ROOT)
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=cwd, capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() or "(working tree clean)"
    except Exception as e:
        return f"[Git error: {e}]"


def git_commit(message: str, repo: str = None) -> str:
    cwd = repo or str(TENGWAR_ROOT)
    try:
        subprocess.run(["git", "add", "-A"], cwd=cwd, capture_output=True, timeout=10)
        result = subprocess.run(
            ["git", "commit", "-m", f"[Tengwar AI] {message}"],
            cwd=cwd, capture_output=True, text=True, timeout=10
        )
        output = result.stdout.strip() or result.stderr.strip()
        memory.store_memory(
            type="self_edit",
            content=f"Git commit in {cwd}: {message}",
            importance=0.9,
            metadata={"output": output[:500], "repo": cwd}
        )
        return output
    except Exception as e:
        return f"[Git error: {e}]"


def git_push(repo: str = None) -> str:
    cwd = repo or str(TENGWAR_ROOT)
    try:
        result = subprocess.run(
            ["git", "push"],
            cwd=cwd, capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip() or result.stderr.strip() or "Pushed."
    except Exception as e:
        return f"[Git push error: {e}]"


def run_tengwar(code: str) -> str:
    """Execute Tengwar code and return the result."""
    # Try Python API first
    try:
        from tengwar import Interpreter
        interp = Interpreter()
        result = interp.run_source(code)
        return str(result) if result is not None else "(no output)"
    except ImportError:
        pass
    # Fallback to subprocess
    try:
        result = subprocess.run(
            ["python3", "-c", f"from tengwar import Interpreter; i=Interpreter(); r=i.run_source({repr(code)}); print(r if r is not None else '')"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            err = result.stderr.strip()
            if err:
                return f"Error: {err.split(chr(10))[-1]}"
        return output or "(no output)"
    except Exception as e:
        return f"Error: {e}"


def get_capabilities_summary() -> str:
    """Return a summary of what the AI can do, for inclusion in prompts."""
    return f"""File access:
  - Read/write files in ~/tengwar-ai/ (your own code) and ~/tengwar/ (the language + website)
  - List directory contents
  - Git status, commit, and push in both repos
  - Execute Tengwar code
  
Your own files: {AI_ROOT}
Tengwar language: {TENGWAR_ROOT}
Website files: {TENGWAR_ROOT}/website/ and {TENGWAR_ROOT}/docs/"""

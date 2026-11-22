from pathlib import Path
from typing import Optional

CANDIDATES = [
    "main.py", "app.py", "server.py", "cli.py",
    "bridge.py", "orchestrator.py", "hunter.py", "run.py"
]


def resolve_entrypoint(repo_path: Path) -> Optional[Path]:
    """Locate the primary executable Python file inside a submodule."""
    if not repo_path.exists():
        return None
    for name in CANDIDATES:
        direct = repo_path / name
        if direct.is_file():
            return direct
    for sub in ("src", "app", "core"):
        sub_dir = repo_path / sub
        if sub_dir.is_dir():
            for name in CANDIDATES:
                nested = sub_dir / name
                if nested.is_file():
                    return nested
    py_files = sorted(repo_path.glob("*.py"))
    return py_files[0] if py_files else None
  

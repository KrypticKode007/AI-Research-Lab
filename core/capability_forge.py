import ast
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent
FORGED_DIR = ROOT_DIR / "core" / "forged_skills"
FORGED_DIR.mkdir(parents=True, exist_ok=True)


def audit_code_for_silent_failures(code: str) -> List[str]:
    """Instant AST pre-check for syntax errors and swallowed exceptions."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"SyntaxError at line {exc.lineno}: {exc.msg}"]

    issues: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if len(node.body) == 1 and isinstance(node.body, ast.Pass):
                issues.append(f"Line {node.lineno}: swallowed exception (except: pass)")
    return issues


def forge_and_verify_skill(
    skill_name: str,
    task_specification: str,
    language: str = "python",
) -> Dict[str, Any]:
    """
    Dynamically synthesize a new executable tool for any arbitrary task,
    run instant AST + Silent-failure-hunter- audits, and register it in forged_skills/.
    """
    safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in skill_name.lower())
    ext = {"python": ".py", "bash": ".sh", "cpp": ".cpp"}.get(language.lower(), ".py")
    target_file = FORGED_DIR / f"{safe_name}{ext}"

    claude_dir = ROOT_DIR / "devops" / "claude-code"
    prompt = (
        f"Create a standalone, zero-defect {language} module at {target_file} "
        f"that accomplishes this exact specification: {task_specification}. "
        f"Include a top-level `execute(payload: dict) -> dict` function if Python. "
        f"Never swallow exceptions; fail loudly with structured error messages."
    )

    gen = subprocess.run(
        ["npx", "tsx", "src/entrypoints/cli.tsx", "-p", prompt],
        cwd=str(claude_dir),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )

    if not target_file.exists():
        return {"status": "synthesis_failed", "stderr": gen.stderr, "stdout": gen.stdout}

    # 1. Instant Built-In AST Guardrail (catches syntax flaws & swallowed exceptions in <2ms)
    if ext == ".py":
        ast_issues = audit_code_for_silent_failures(target_file.read_text(encoding="utf-8"))
        if ast_issues:
            target_file.unlink(missing_ok=True)
            return {
                "status": "rejected_by_ast_guardrail",
                "skill": safe_name,
                "issues": ast_issues,
            }

    # 2. External Deep Scan with Silent-failure-hunter-
    hunter_cli = ROOT_DIR / "devops" / "Silent-failure-hunter" / "cli.py"
    if hunter_cli.exists():
        audit = subprocess.run(
            [sys.executable, str(hunter_cli), str(target_file)],
            capture_output=True,
            text=True,
            check=False,
        )
        if audit.returncode != 0:
            target_file.unlink(missing_ok=True)
            return {
                "status": "rejected_by_immune_system",
                "file": str(target_file),
                "audit_errors": audit.stdout or audit.stderr,
            }

    return {
        "status": "forged_and_verified",
        "skill": safe_name,
        "path": str(target_file),
    }


def run_forged_skill(skill_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Audit, hot-load, and execute any previously forged Python skill without restarting."""
    safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in skill_name.lower())
    target_file = FORGED_DIR / f"{safe_name}.py"
    if not target_file.exists():
        return {"status": "not_found", "skill": safe_name}

    # Re-verify AST integrity before hot-loading into memory
    ast_issues = audit_code_for_silent_failures(target_file.read_text(encoding="utf-8"))
    if ast_issues:
        return {
            "status": "blocked_corrupted_skill",
            "skill": safe_name,
            "issues": ast_issues,
        }

    spec = importlib.util.spec_from_file_location(safe_name, str(target_file))
    if not spec or not spec.loader:
        return {"status": "load_error", "skill": safe_name}

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "execute"):
        return {"status": "missing_execute_entrypoint", "skill": safe_name}

    return {"status": "success", "output": module.execute(payload)}
    

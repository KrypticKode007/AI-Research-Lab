import subprocess
from pathlib import Path
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from core.entry_resolver import resolve_entrypoint
from core.capability_forge import (
    FORGED_DIR,
    forge_and_verify_skill,
    run_forged_skill,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
mcp = FastMCP("Kryptic-Omni-Orchestrator")


def _run_cmd(cmd: list[str], cwd: Path = ROOT_DIR, timeout: int = 60) -> Dict[str, Any]:
    """Execute a subprocess safely without swallowing errors."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"returncode": -1, "stdout": "", "stderr": f"CRITICAL_BRIDGE_ERROR: {exc}"}


def _run_repo(rel_path: str, args: list[str] | None = None, timeout: int = 60) -> Dict[str, Any]:
    """Resolve a submodule's entry point dynamically and execute it."""
    repo_dir = ROOT_DIR / rel_path
    entry = resolve_entrypoint(repo_dir)
    if not entry:
        return {"returncode": -1, "stdout": "", "stderr": f"Entrypoint not found in {rel_path}"}
    return _run_cmd(["python3", str(entry)] + (args or []), cwd=entry.parent, timeout=timeout)


# --- 1. COGNITIVE & MEMORY LAYER ---
@mcp.tool()
def query_holonomic_memory(prompt: str) -> Dict[str, Any]:
    """Route context queries through Holonomic-Sentience-Core."""
    return _run_repo("core/Holonomic-Sentience", ["--query", prompt])


# --- 2. MACOS & ANDROID INTERFACE LAYER ---
@mcp.tool()
def control_android_device(action: str = "mirror", args: str = "") -> Dict[str, Any]:
    """Launch scrcpy or invoke kai-007 automation on macOS / Android 15+."""
    if action == "mirror":
        scrcpy_bin = ROOT_DIR / "interfaces" / "scrcpy" / "scrcpy"
        bin_path = str(scrcpy_bin) if scrcpy_bin.exists() else "scrcpy"
        subprocess.Popen([bin_path] + (args.split() if args else []))
        return {"status": "launched", "target": bin_path}

    kai_dir = ROOT_DIR / "interfaces" / "kai-007"
    return _run_cmd(["bash", "kai.sh", action, args], cwd=kai_dir)


# --- 3. DOMAIN MICROSERVICES LAYER ---
@mcp.tool()
def master_audio_track(input_path: str, reference_path: str) -> Dict[str, Any]:
    """Trigger PatchPilot audio mastering job."""
    return _run_repo(
        "services/PatchPilot",
        ["--target", input_path, "--reference", reference_path],
        timeout=300,
    )


@mcp.tool()
def run_nkryptd_intel_scan(scope: str = "full") -> Dict[str, Any]:
    """Execute -nkryptd cyber-resilience and business intelligence pipeline."""
    return _run_repo("services/nkryptd", ["--mode", scope])


# --- 4. EDGE, ROBOTICS & BATTERY TELEMETRY LAYER ---
@mcp.tool()
def dispatch_rosa_command(ros_command: str) -> Dict[str, Any]:
    """Forward natural-language robotics directives to golden-rosa-template."""
    return _run_repo("edge/golden-rosa-template", ["--cmd", ros_command])


@mcp.tool()
def check_edge_homeostasis() -> Dict[str, Any]:
    """Poll bio-edge-organism SNN state and Autonomous-self-healing-battery health."""
    return {
        "bio_edge": _run_repo("edge/bio-edge-organism"),
        "battery_system": _run_repo("edge/self-healing-battery"),
    }


# --- 5. SELF-HEALING DEVOPS & CODE IMMUNE SYSTEM ---
@mcp.tool()
def audit_and_heal_workspace(target_repo: str = ".", auto_fix: bool = False) -> Dict[str, Any]:
    """Run Silent-failure-hunter- across submodules; optionally invoke claude-code."""
    scan_path = (ROOT_DIR / target_repo).resolve()
    audit = _run_repo("devops/Silent-failure-hunter", [str(scan_path)])

    result: Dict[str, Any] = {"audit": audit}
    if auto_fix and audit["returncode"] != 0:
        claude_dir = ROOT_DIR / "devops" / "claude-code"
        fix_prompt = f"Fix all silent failures detected in {scan_path}:\n{audit['stdout']}"
        result["auto_patch"] = _run_cmd(
            ["npx", "tsx", "src/entrypoints/cli.tsx", "-p", fix_prompt],
            cwd=claude_dir,
            timeout=300,
        )
    return result


# --- 6. UNIVERSAL CAPABILITY FORGE (DYNAMIC SKILL SYNTHESIS) ---
@mcp.tool()
def synthesize_new_capability(
    skill_name: str, task_specification: str, language: str = "python"
) -> Dict[str, Any]:
    """Build, audit, and register a brand-new tool on the fly for any unforeseen task."""
    return forge_and_verify_skill(skill_name, task_specification, language)


@mcp.tool()
def execute_forged_capability(skill_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Hot-load and run any previously synthesized skill in core/forged_skills/."""
    return run_forged_skill(skill_name, payload)


@mcp.tool()
def list_forged_capabilities() -> List[str]:
    """List all dynamically synthesized skills currently available in the forge."""
    if not FORGED_DIR.exists():
        return []
    return sorted(
        f.stem for f in FORGED_DIR.iterdir() if f.is_file() and f.name != "__init__.py"
    )


if __name__ == "__main__":
    mcp.run()
                

import asyncio
import json
import os
import subprocess
from core.entry_resolver 
import resolve_entrypoint
from pathlib import Path
from typing import Any, Dict

# Standard MCP stdio / FastMCP compatible bridge
from mcp.server.fastmcp import FastMCP

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


# --- 1. COGNITIVE & MEMORY LAYER ---
@mcp.tool()
def query_holonomic_memory(prompt: str) -> Dict[str, Any]:
    """Route context queries through Holonomic-Sentience-Core & Advanced-Ai-Model."""
    target = ROOT_DIR / "core" / "Holonomic-Sentience"
    return _run_cmd(["python3", "-m", "holonomic_core", "--query", prompt], cwd=target)


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
    patch_dir = ROOT_DIR / "services" / "PatchPilot"
    return _run_cmd(
        ["python3", "cli.py", "--target", input_path, "--reference", reference_path],
        cwd=patch_dir,
        timeout=300,
    )


@mcp.tool()
def run_nkryptd_intel_scan(scope: str = "full") -> Dict[str, Any]:
    """Execute -nkryptd cyber-resilience and business intelligence pipeline."""
    nk_dir = ROOT_DIR / "services" / "nkryptd"
    return _run_cmd(["python3", "main.py", "--mode", scope], cwd=nk_dir)


# --- 4. EDGE, ROBOTICS & BATTERY TELEMETRY LAYER ---
@mcp.tool()
def dispatch_rosa_command(ros_command: str) -> Dict[str, Any]:
    """Forward natural-language robotics directives to golden-rosa-template."""
    rosa_dir = ROOT_DIR / "edge" / "golden-rosa-template"
    return _run_cmd(["python3", "rosa_bridge.py", "--cmd", ros_command], cwd=rosa_dir)


@mcp.tool()
def check_edge_homeostasis() -> Dict[str, Any]:
    """Poll bio-edge-organism SNN state and Autonomous-self-healing-battery health."""
    bio = _run_cmd(
        ["python3", "status.py"], cwd=ROOT_DIR / "edge" / "bio-edge-organism"
    )
    bat = _run_cmd(
        ["python3", "diagnostics.py"], cwd=ROOT_DIR / "edge" / "self-healing-battery"
    )
    return {"bio_edge": bio, "battery_system": bat}


# --- 5. SELF-HEALING DEVOPS & CODE IMMUNE SYSTEM ---
@mcp.tool()
def audit_and_heal_workspace(target_repo: str = ".", auto_fix: bool = False) -> Dict[str, Any]:
    """Run Silent-failure-hunter- & Bug-away across submodules; optionally invoke claude-code."""
    scan_path = (ROOT_DIR / target_repo).resolve()
    hunter_dir = ROOT_DIR / "devops" / "Silent-failure-hunter"
    audit = _run_cmd(["python3", "hunter.py", str(scan_path)], cwd=hunter_dir)

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


if __name__ == "__main__":
    mcp.run()

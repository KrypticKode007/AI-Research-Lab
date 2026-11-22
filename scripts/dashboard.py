#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns

ROOT_DIR = Path(__file__).resolve().parent.parent
console = Console()

EMBLEMS = {
    "KAI-007": """[bold cyan]
   [ ◉_◉ ]  KAI-007 OS
  /|=====|\\ macOS + Android 15+
   /     \\  OFFLINE SHELL BRIDGE[/bold cyan]""",
    "BIO-EDGE": """[bold green]
   ⚡<SNN>⚡ BIO-EDGE ORGANISM
   [90.97ns] C++11 / ESP32 CORE
   ~HOMEOSTASIS: ACTIVE~[/bold green]""",
    "FORGE": """[bold yellow]
    ⚒️ [FORGE] ⚒️ CAPABILITY ENGINE
   SYNTH -> AUDIT -> HOT-RELOAD
   STATUS: ZERO DEAD ENDS[/bold yellow]""",
    "IMMUNE": """[bold magenta]
   🛡️ [IMMUNE] 🛡️ SILENT-HUNTER
   AST SCAN + CLAUDE-CODE PATCH
   FAIL LOUD, NEVER SILENT[/bold magenta]""",
}


def check_daemon() -> str:
    res = subprocess.run(
        ["launchctl", "list"], capture_output=True, text=True, check=False
    )
    return "[bold green]ONLINE (launchd)[/bold green]" if "com.kryptic.omni-orchestrator" in res.stdout else "[bold yellow]STANDBY[/bold yellow]"


def render_dashboard() -> None:
    ascii_file = ROOT_DIR / "assets" / "kryptic_omni_core.ascii"
    if ascii_file.exists():
        console.print(f"[bold bright_cyan]{ascii_file.read_text()}[/bold bright_cyan]")

    # Render Custom Module Emblems
    panels = [Panel(art, border_style="bright_blue", expand=True) for art in EMBLEMS.values()]
    console.print(Columns(panels))

    # Render Live Subsystem Telemetry Table
    table = Table(title="KRYPTIC OMNI-CORE // SUBSYSTEM MATRIX", border_style="cyan", expand=True)
    table.add_column("Layer", style="bold white")
    table.add_column("Bound Repositories", style="bright_blue")
    table.add_column("Mount Status", justify="center")

    layers = [
        ("Cognitive Core", "Golden-Agent, Holonomic-Sentience, Advanced-Ai-Model", "core/Golden-Agent"),
        ("OS & Device Bridge", "kai-007, scrcpy", "interfaces/kai-007"),
        ("Domain Microservices", "PatchPilot, -nkryptd, CERN ROOT", "services/PatchPilot"),
        ("Edge & Robotics", "golden-rosa-template, bio-edge-organism, Smart-Battery", "edge/bio-edge-organism"),
        ("Immune & DevOps", "Bug-away, Silent-failure-hunter-, claude-code", "devops/Silent-failure-hunter"),
    ]

    for layer, repos, check_path in layers:
        mounted = (ROOT_DIR / check_path).exists()
        status = "[bold green]● MOUNTED[/bold green]" if mounted else "[bold red]○ PENDING SETUP[/bold red]"
        table.add_row(layer, repos, status)

    forged_dir = ROOT_DIR / "core" / "forged_skills"
    skill_count = len([f for f in forged_dir.glob("*.py") if f.name != "__init__.py"]) if forged_dir.exists() else 0
    table.add_row("Capability Forge", f"Dynamic Skill Synthesizer ({skill_count} forged skills)", "[bold cyan]★ ARMED[/bold cyan]")
    table.add_row("macOS Supervisor", "com.kryptic.omni-orchestrator", check_daemon())

    console.print(table)


if __name__ == "__main__":
    render_dashboard()

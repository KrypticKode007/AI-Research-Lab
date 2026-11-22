cp core/capability_forge.py core/capability_forge.py.bak 2>/dev/null || true

cat << 'EOF' > core/capability_forge.py
"""
Kryptic Omni-Core — Just-In-Time Capability Forge (REQ-02 / IF-01)
Synthesizes, AST-audits, snapshots, and hot-loads Python capability modules
into the live Golden-Agent MCP tool registry without restarting.
"""

import importlib.util
import json
import logging
import shutil
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, Optional

from core.ast_sandbox import AuditResult, audit_source

logger = logging.getLogger("omni.capability_forge")


class SecurityError(Exception):
    """Raised when synthesized code violates AST sandbox policies."""


class ForgeBuildError(Exception):
    """Raised when synthesized module fails validation or runtime loading."""


@dataclass
class ForgedCapability:
    name: str
    filepath: str
    entrypoint: str
    audit_node_count: int
    loaded_at: float
    version: int = 1


class CapabilityForge:
    """Closed-loop JIT tool synthesizer and AST-gated MCP hot-loader."""

    def __init__(
        self,
        forge_dir: str = "core/forged_tools",
        snapshot_dir: str = "core/.forge_snapshots",
        max_ast_nodes: int = 2500,
    ) -> None:
        self.forge_dir = Path(forge_dir)
        self.snapshot_dir = Path(snapshot_dir)
        self.max_ast_nodes = max_ast_nodes

        self.forge_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        self._registry: Dict[str, Callable[..., Any]] = {}
        self._manifests: Dict[str, ForgedCapability] = {}

    def _sanitize_name(self, tool_name: str) -> str:
        clean = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in tool_name.strip())
        if not clean or clean.isdigit():
            raise ForgeBuildError(f"Invalid capability identifier: '{tool_name}'")
        return clean.lower()

    def _backup_existing(self, target_path: Path, safe_name: str) -> Optional[Path]:
        if not target_path.exists():
            return None
        ts = int(time.time())
        backup_path = self.snapshot_dir / f"{safe_name}.{ts}.bak.py"
        shutil.copy2(target_path, backup_path)
        return backup_path

    def _rollback(self, target_path: Path, backup_path: Optional[Path], mod_name: str) -> None:
        sys.modules.pop(mod_name, None)
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, target_path)
            logger.warning("Rolled back '%s' from snapshot %s", target_path, backup_path)
        elif target_path.exists():
            target_path.unlink()

    def forge_and_load(
        self,
        tool_name: str,
        synthesized_code: str,
        entrypoint: str = "run",
    ) -> ForgedCapability:
        """
        Full JIT pipeline:
        1. Sanitize tool identifier
        2. Run static AST security audit (REQ-02)
        3. Snapshot prior version for atomic rollback
        4. Dynamically import & bind entrypoint into live MCP registry
        """
        safe_name = self._sanitize_name(tool_name)

        # Gate 1: Mandatory AST Security Audit before touching disk
        audit: AuditResult = audit_source(synthesized_code, max_nodes=self.max_ast_nodes)
        if not audit.safe:
            logger.error("AST Sandbox rejected '%s': %s", safe_name, audit.violations)
            raise SecurityError(
                f"Capability Forge AST audit rejected '{safe_name}': {audit.violations}"
            )

        target_path = self.forge_dir / f"{safe_name}.py"
        mod_name = f"forged_tools.{safe_name}"
        backup_path = self._backup_existing(target_path, safe_name)

        try:
            target_path.write_text(synthesized_code, encoding="utf-8")

            # Hot-reload module cleanly
            sys.modules.pop(mod_name, None)
            spec = importlib.util.spec_from_file_location(mod_name, str(target_path))
            if spec is None or spec.loader is None:
                raise ForgeBuildError(f"Unable to build module spec for {target_path}")

            module: ModuleType = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)

            fn = getattr(module, entrypoint, None)
            if not callable(fn):
                raise ForgeBuildError(
                    f"Module '{safe_name}' missing callable entrypoint '{entrypoint}()'"
                )

            prev_version = self._manifests[safe_name].version if safe_name in self._manifests else 0
            manifest = ForgedCapability(
                name=safe_name,
                filepath=str(target_path),
                entrypoint=entrypoint,
                audit_node_count=audit.node_count,
                loaded_at=time.time(),
                version=prev_version + 1,
            )

            self._registry[safe_name] = fn
            self._manifests[safe_name] = manifest
            logger.info(
                "Hot-loaded capability '%s' v%d (%d AST nodes)",
                safe_name,
                manifest.version,
                manifest.audit_node_count,
            )
            return manifest

        except Exception as exc:
            self._rollback(target_path, backup_path, mod_name)
            if isinstance(exc, (SecurityError, ForgeBuildError)):
                raise
            raise ForgeBuildError(f"Hot-load failed for '{safe_name}': {exc}") from exc

    def invoke(self, tool_name: str, **kwargs: Any) -> Any:
        safe_name = self._sanitize_name(tool_name)
        if safe_name not in self._registry:
            raise KeyError(f"Capability '{safe_name}' is not registered in live MCP hub")
        return self._registry[safe_name](**kwargs)

    def list_capabilities(self) -> Dict[str, Dict[str, Any]]:
        return {name: asdict(meta) for name, meta in self._manifests.items()}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    forge = CapabilityForge()

    # 1. Valid synthesized tool -> passes AST gate and hot-loads
    sample_tool = (
        "import json, math\n"
        "def run(values: list) -> str:\n"
        "    rms = math.sqrt(sum(v * v for v in values) / max(len(values), 1))\n"
        "    return json.dumps({'rms': round(rms, 4)})\n"
    )
    cap = forge.forge_and_load("signal_rms", sample_tool)
    print("Loaded:", cap)
    print("Output:", forge.invoke("signal_rms", values=[3.0, 4.0]))

    # 2. Malicious synthesized tool -> blocked before touching disk
    try:
        forge.forge_and_load("bad_tool", "import os\ndef run(): os.system('whoami')\n")
    except SecurityError as err:
        print("Blocked as expected:", err)
EOF

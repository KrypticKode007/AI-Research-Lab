cat << 'EOF' > core/ast_sandbox.py
"""
Kryptic Omni-Core — Capability Forge AST Sandbox Validator (REQ-02)
Performs static Abstract Syntax Tree inspection on JIT-synthesized Python tools
prior to runtime MCP hot-loading.
"""

import ast
from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class AuditResult:
    safe: bool
    violations: List[str] = field(default_factory=list)
    node_count: int = 0


class CapabilityASTSandbox(ast.NodeVisitor):
    """Static AST policy enforcement for dynamically synthesized tool modules."""

    BLOCKED_IMPORTS: Set[str] = {
        "os", "sys", "subprocess", "shutil", "socket", "pty",
        "ctypes", "importlib", "pickle", "marshal", "builtins",
        "urllib", "requests", "http", "ftplib", "telnetlib", "webbrowser",
    }

    BLOCKED_CALLS: Set[str] = {
        "eval", "exec", "compile", "__import__", "open",
        "getattr", "setattr", "delattr", "globals", "locals",
        "vars", "breakpoint", "input", "memoryview",
    }

    BLOCKED_ATTRIBUTES: Set[str] = {
        "__subclasses__", "__bases__", "__mro__", "__globals__",
        "__builtins__", "__code__", "__closure__", "__func__",
        "__self__", "__dict__", "__class__", "system", "popen",
    }

    def __init__(self, max_nodes: int = 2500) -> None:
        self.max_nodes = max_nodes
        self.violations: List[str] = []
        self.node_count = 0

    def generic_visit(self, node: ast.AST) -> None:
        self.node_count += 1
        if self.node_count > self.max_nodes:
            self.violations.append(
                f"Complexity limit exceeded: >{self.max_nodes} AST nodes"
            )
            return
        super().generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root_pkg = alias.name.split(".")[0]
            if root_pkg in self.BLOCKED_IMPORTS:
                self.violations.append(
                    f"Line {node.lineno}: Blocked import '{alias.name}'"
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            root_pkg = node.module.split(".")[0]
            if root_pkg in self.BLOCKED_IMPORTS:
                self.violations.append(
                    f"Line {node.lineno}: Blocked import-from '{node.module}'"
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Check direct function calls: eval(...), exec(...)
        if isinstance(node.func, ast.Name):
            if node.func.id in self.BLOCKED_CALLS:
                self.violations.append(
                    f"Line {node.lineno}: Blocked builtin call '{node.func.id}()'"
                )
        # Check attribute calls: os.system(...), obj.__subclasses__()
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in self.BLOCKED_CALLS or node.func.attr in self.BLOCKED_ATTRIBUTES:
                self.violations.append(
                    f"Line {node.lineno}: Blocked method call '.{node.func.attr}()'"
                )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in self.BLOCKED_ATTRIBUTES:
            self.violations.append(
                f"Line {node.lineno}: Blocked dunder/attribute access '.{node.attr}'"
            )
        self.generic_visit(node)


def audit_source(source_code: str, max_nodes: int = 2500) -> AuditResult:
    """Parse and audit synthesized Python source code before hot-loading."""
    try:
        tree = ast.parse(source_code)
    except SyntaxError as exc:
        return AuditResult(
            safe=False,
            violations=[f"SyntaxError at line {exc.lineno}: {exc.msg}"],
            node_count=0,
        )

    validator = CapabilityASTSandbox(max_nodes=max_nodes)
    validator.visit(tree)
    return AuditResult(
        safe=len(validator.violations) == 0,
        violations=validator.violations,
        node_count=validator.node_count,
    )
EOF

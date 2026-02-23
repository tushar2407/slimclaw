#!/usr/bin/env python3
"""Lint: fail if code uses relative path string literals (require absolute paths)."""
from __future__ import annotations

import ast
import sys
from pathlib import Path


def looks_relative(s: str) -> bool:
    """True if string looks like a relative path (not absolute)."""
    if not s or not isinstance(s, str):
        return False
    s = s.strip()
    # Absolute: starts with / (Unix) or drive letter (Windows)
    if s.startswith("/"):
        return False
    if len(s) >= 2 and s[1] == ":" and s[0].isalpha():
        return False
    return True


def check_node(node: ast.AST, path: Path, issues: list[tuple[int, str]]) -> None:
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name == "open" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if looks_relative(arg.value):
                        issues.append(
                            (node.lineno, f"open({arg.value!r}): use absolute path")
                        )
            elif name == "Path" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if looks_relative(arg.value):
                        issues.append(
                            (node.lineno, f"Path({arg.value!r}): use absolute path")
                        )
    for child in ast.iter_child_nodes(node):
        check_node(child, path, issues)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    scripts_dir = root / "scripts"
    all_issues: list[tuple[Path, int, str]] = []

    for path in root.rglob("*.py"):
        if path == Path(__file__):
            continue
        if scripts_dir in path.parents:
            continue
        try:
            tree = ast.parse(path.read_text(), filename=str(path))
        except SyntaxError as e:
            print(f"{path}:{e.lineno}: syntax error: {e}", file=sys.stderr)
            return 1
        issues: list[tuple[int, str]] = []
        check_node(tree, path, issues)
        for line, msg in issues:
            all_issues.append((path, line, msg))

    if not all_issues:
        return 0

    for path, line, msg in sorted(all_issues):
        rel = path.relative_to(root)
        print(f"{rel}:{line}: {msg}", file=sys.stderr)
    print("\nUse absolute paths or Path(__file__).parent / 'name', Path.home(), etc.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

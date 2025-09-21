#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import subprocess
import sys
from dataclasses import dataclass
from typing import List

ALLOWED_FROM_MODULE = "sciv.game"
ALLOWED_NAME = "OpenCiv"


@dataclass
class Violation:
    path: str
    lineno: int
    col: int
    message: str
    line_preview: str


def _run_git(args: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git"] + args, check=False, capture_output=True, text=True)


def _staged_py_files() -> List[str]:
    res = _run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMRT"])
    if res.returncode != 0:
        print("pre-commit(block-back-imports): failed to list staged files.", file=sys.stderr)
        sys.exit(2)
    files = [p.strip() for p in res.stdout.splitlines() if p.strip()]
    return [p for p in files if p.endswith(".py") or p.endswith(".pyi")]


def _read_staged_file(path: str) -> str | None:
    res: subprocess.CompletedProcess[str] = _run_git(["show", f":{path}"])
    if res.returncode != 0:
        return None
    return res.stdout


def _is_allowed_from_import(node: ast.ImportFrom) -> bool:
    if node.level != 0:
        return False
    if node.module != ALLOWED_FROM_MODULE:
        return False
    if len(node.names) != 1:
        return False
    alias = node.names[0]
    if alias.asname is not None:
        return False
    return alias.name == ALLOWED_NAME


def _check_source(path: str, source: str) -> List[Violation]:
    violations: List[Violation] = []
    try:
        tree = ast.parse(source, filename=path, type_comments=True)
    except SyntaxError as _:
        lines = source.splitlines()
        for idx, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if stripped.startswith("import sciv") or stripped.startswith("from sciv"):
                violations.append(
                    Violation(
                        path=path,
                        lineno=idx,
                        col=1,
                        message="Forbidden import from 'sciv' (syntax-error fallback).",
                        line_preview=raw,
                    )
                )
        return violations

    lines: List[str] = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name or ""
                if name == "sciv" or name.startswith("sciv."):
                    violations.append(
                        Violation(
                            path=path,
                            lineno=getattr(node, "lineno", 1),
                            col=getattr(node, "col_offset", 0) + 1,
                            message="Forbidden 'import sciv[...]' usage.",
                            line_preview=lines[getattr(node, "lineno", 1) - 1]
                            if 1 <= getattr(node, "lineno", 1) <= len(lines)
                            else "",
                        )
                    )

        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "sciv" or mod.startswith("sciv."):
                if _is_allowed_from_import(node):
                    continue
                violations.append(
                    Violation(
                        path=path,
                        lineno=getattr(node, "lineno", 1),
                        col=getattr(node, "col_offset", 0) + 1,
                        message="Forbidden 'from sciv[...] import ...' usage (only 'from sciv.game import OpenCiv' is allowed).",
                        line_preview=lines[getattr(node, "lineno", 1) - 1]
                        if 1 <= getattr(node, "lineno", 1) <= len(lines)
                        else "",
                    )
                )

    return violations


def main() -> int:
    py_files: List[str] = _staged_py_files()
    if not py_files:
        return 0

    all_violations: List[Violation] = []
    for path in py_files:
        content: str | None = _read_staged_file(path)
        if content is None:
            continue
        all_violations.extend(_check_source(path, content))

    if all_violations:
        print("\n⛔ Commit blocked: disallowed 'sciv' imports found.\n", file=sys.stderr)
        print("Only this is allowed:\n    from sciv.game import OpenCiv\n", file=sys.stderr)
        for v in all_violations:
            loc = f"{v.path}:{v.lineno}:{v.col}"
            print(f"- {loc}  {v.message}", file=sys.stderr)
            if v.line_preview.strip():
                print(f"    {v.line_preview.rstrip()}", file=sys.stderr)
        print(
            "\nFix the imports (use relative or package-local imports) and try committing again.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

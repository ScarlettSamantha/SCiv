#!/usr/bin/env python3
import gzip
import json
import pydoc
import re
import sys
from argparse import ArgumentParser
from io import StringIO
from sys import getsizeof
from typing import Any, Dict, List, Optional, Set, Tuple

# ANSI color codes
COLOR_RESET = "\033[0m"
COLOR_MAP = {
    "int": "\033[33m",  # yellow
    "float": "\033[36m",  # cyan
    "bool": "\033[35m",  # magenta
    "str": "\033[32m",  # green
    "NoneType": "\033[90m",  # bright black
    "dict": "\033[31m",  # red
    "list": "\033[31m",  # red
    "tuple": "\033[31m",  # red
    "set": "\033[31m",  # red
}
NAME_COLOR = "\033[95m"
CLASS_COLOR = "\033[94m"
LEVEL_COLORS = ["\033[97m", "\033[94m", "\033[92m", "\033[93m", "\033[95m", "\033[96m"]


def _build_prefix(markers: List[bool], is_last: bool) -> str:
    prefix = ""
    for has_sib in markers[:-1]:
        prefix += "│   " if has_sib else "    "
    if markers:
        prefix += "└── " if is_last else "├── "
    return prefix


def is_atomic(obj: Any) -> bool:
    return isinstance(obj, (int, float, bool, str, type(None)))


def inspect_json(
    obj: Any,
    name: str = "root",
    markers: Optional[List[bool]] = None,
    seen: Optional[Set[int]] = None,
    is_last: bool = True,
) -> None:
    if markers is None:
        markers = []
    if seen is None:
        seen = set()

    oid = id(obj)
    prefix = _build_prefix(markers, is_last)
    lvl = max(0, len(markers) - 1)
    if COLOR_ENABLED:
        prefix = f"{LEVEL_COLORS[lvl % len(LEVEL_COLORS)]}{prefix}{COLOR_RESET}"

    local = name.split(".")[-1]
    name_col = f"{LEVEL_COLORS[lvl % len(LEVEL_COLORS)]}{local}{COLOR_RESET}" if COLOR_ENABLED else local
    typ = type(obj).__name__
    type_col = f"{COLOR_MAP.get(typ, NAME_COLOR)}{typ}{COLOR_RESET}"

    if is_atomic(obj):
        print(f"{prefix}{name_col} ({type_col}): {repr(obj)}")
        return

    if oid in seen:
        print(f"{prefix}{name_col} ({type_col}): <circular ref>")
        return
    seen.add(oid)

    # 3) Recurse
    print(f"{prefix}{name_col} ({type_col}):")
    if isinstance(obj, dict):
        items = list(obj.items())  # type: ignore
        for idx, (k, v) in enumerate(items):  # type: ignore
            last = idx == len(items) - 1  # type: ignore
            # preserve any __ref__-style keys verbatim
            if k in ("__ref__", "__objref__", "__cycle_ref__", "__class__", "__module__"):
                key_col = f"{NAME_COLOR}{k}{COLOR_RESET}"
                print(f"{prefix}    {key_col}: {v}")
            else:
                inspect_json(v, f"{name}.{k}", markers + [not last], seen, last)

    elif isinstance(obj, (list, tuple, set)):
        seq = list(obj)  # type: ignore
        for idx, v in enumerate(seq):  # type: ignore
            last = idx == len(seq) - 1  # type: ignore
            inspect_json(v, f"{name}[{idx}]", markers + [not last], seen, last)

    else:
        # fallback for other types
        print(f"{prefix}    {repr(obj)}")


def load_json(path: str) -> Any:
    if path.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    else:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


def collect_stats(obj: Any) -> Dict[str, Any]:
    seen: Set[int] = set()
    stats: Dict[str, Any] = {"total_nodes": 0, "type_counts": {}, "ref_counts": {}, "size_map": {}}

    def _rec(obj: Any, path: str = "root"):
        oid = id(obj)
        stats["ref_counts"][oid] = stats["ref_counts"].get(oid, 0) + 1
        if oid in seen:
            return
        seen.add(oid)
        typ = type(obj).__name__
        stats["type_counts"][typ] = stats["type_counts"].get(typ, 0) + 1
        stats["total_nodes"] += 1
        try:
            size = getsizeof(obj)
        except Exception:
            size = 0
        stats["size_map"][oid] = (path, typ, size)
        if is_atomic(obj):
            return
        if isinstance(obj, dict):
            for k, v in obj.items():  # type: ignore
                _rec(v, f"{path}[{repr(k)}]")  # type: ignore
        elif isinstance(obj, (list, tuple, set)):
            for i, v in enumerate(obj):  # type: ignore
                _rec(v, f"{path}[{i}]")

    _rec(obj)
    return stats


def show_summary(data: Any) -> None:
    print("Summary of root:")
    if isinstance(data, dict):
        print(f"  type: dict, top-level keys: {list(data.keys())}")  # type: ignore
    elif isinstance(data, (list, tuple, set)):
        print(f"  type: {type(data).__name__}, length: {len(data)}")  # type: ignore
    else:
        print(f"  type: {type(data).__name__}")
    print()
    stats = collect_stats(data)
    print(f"Total nodes visited: {stats['total_nodes']}")
    print("Top types:")
    for t, c in sorted(stats["type_counts"].items(), key=lambda x: -x[1])[:5]:
        print(f"  {t}: {c}")
    print("Biggest objects:")
    for path, typ, sz in sorted(stats["size_map"].values(), key=lambda x: -x[2])[:5]:
        print(f"  {path} ({typ}): {sz} bytes")


def find_matches(obj: Any, path: str, regex: re.Pattern[str], matches: List[Tuple[str, Any]]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():  # type: ignore
            newp = f"{path}[{repr(k)}]"  # type: ignore
            if regex.fullmatch(newp):
                matches.append((newp, v))  # type: ignore
            find_matches(v, newp, regex, matches)
    elif isinstance(obj, (list, tuple, set)):
        for i, v in enumerate(obj):  # type: ignore
            newp = f"{path}[{i}]"
            if regex.fullmatch(newp):
                matches.append((newp, v))  # type: ignore
            find_matches(v, newp, regex, matches)


def capture_subtree(obj: Any, path: str) -> str:
    buf = StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        inspect_json(obj, name=path)
    finally:
        sys.stdout = old
    return buf.getvalue()


# Main CLI


def main():
    parser = ArgumentParser(description="Inspect JSON dump of serialized entities")
    parser.add_argument("path", help="Path to JSON file")
    parser.add_argument("--color", action="store_true", help="Enable colors")
    parser.add_argument("--no-pager", action="store_true", help="Disable pager")
    parser.add_argument("-q", "--query", help="Regex to filter subtrees")
    parser.add_argument("--summary", action="store_true", help="Show summary stats")
    args = parser.parse_args()
    global COLOR_ENABLED
    COLOR_ENABLED = args.color
    data = load_json(args.path)
    if args.summary:
        show_summary(data)
        sys.exit(0)
    if args.query:
        try:
            regex = re.compile(args.query)
        except re.error as e:
            print(f"Invalid regex: {e}", file=sys.stderr)
            sys.exit(1)
        matches: List[Tuple[str, Any]] = []
        find_matches(data, "root", regex, matches)
        if not matches:
            print(f"No paths matched /{args.query}/", file=sys.stderr)
            sys.exit(1)
        output = "\n".join(capture_subtree(v, p) for p, v in matches)
    else:
        buf = StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            inspect_json(data)
        finally:
            sys.stdout = old
        output = buf.getvalue()
    if args.no_pager:
        sys.stdout.write(output)
    else:
        pydoc.pager(output)


if __name__ == "__main__":
    main()

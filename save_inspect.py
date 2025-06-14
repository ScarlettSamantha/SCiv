#!/usr/bin/env python3
import gzip
import dill
import sys
import re
import pydoc
from io import StringIO
from argparse import ArgumentParser
from sys import getsizeof
from typing import Any, Dict, List, Optional, Set, Tuple

# ANSI color codes
COLOR_RESET = "\033[0m"
COLOR_MAP = {
    "int": "\033[33m",  # yellow
    "float": "\033[36m",  # cyan
    "bool": "\033[35m",  # magenta
    "str": "\033[32m",  # green
    "bytes": "\033[34m",  # blue
    "NoneType": "\033[90m",  # bright black
    "dict": "\033[31m",  # red
    "list": "\033[31m",  # red
    "tuple": "\033[31m",  # red
    "set": "\033[31m",  # red
    "object": "\033[37m",  # white
}

NAME_COLOR = "\033[95m"
CLASS_COLOR = "\033[94m"

LEVEL_COLORS = [
    "\033[97m",
    "\033[94m",
    "\033[92m",
    "\033[93m",
    "\033[95m",
    "\033[96m",
]
uuid_path = "saves/{uuid}/data.pickle.gz"
direct_path = "saves/{name}/data.pickle.gz"


def is_atomic(obj: Any) -> bool:
    return isinstance(obj, (int, float, bool, str, bytes, type(None)))


def _build_prefix(markers: List[bool], is_last: bool) -> str:
    prefix = ""
    for has_sib in markers[:-1]:
        prefix += "│   " if has_sib else "    "
    if markers:
        prefix += "└── " if is_last else "├── "
    return prefix


def inspect_obj(
    obj: Any,
    name: str = "root",
    markers: Optional[List[bool]] = None,
    seen: Optional[Dict[int, str]] = None,
    is_last: bool = True,
) -> None:
    if markers is None:
        markers = []
    if seen is None:
        seen = {}

    oid = id(obj)
    prefix = _build_prefix(markers, is_last)
    lvl = max(0, len(markers) - 1)
    if COLOR_ENABLED:
        prefix = f"{LEVEL_COLORS[lvl % len(LEVEL_COLORS)]}{prefix}{COLOR_RESET}"

    # local name highlight
    parts = re.split(r"[.\[]", name)
    local = parts[-1].rstrip("]")
    name_col = f"{LEVEL_COLORS[lvl % len(LEVEL_COLORS)]}{local}{COLOR_RESET}" if COLOR_ENABLED else local

    # type highlight
    typ = type(obj).__name__
    type_col = f"{CLASS_COLOR}{typ}{COLOR_RESET}" if COLOR_ENABLED else typ

    # handle circular refs with path marker
    if is_atomic(obj):
        shallow = getsizeof(obj)
        try:
            pickled = len(dill.dumps(obj))  # type: ignore
        except Exception:
            pickled = -1
        size_info = f"shallow={shallow}B" + (f", pickled={pickled}B" if pickled >= 0 else "")
        print(f"{prefix}{name_col} ({type_col}, {size_info}): {repr(obj)}")
        return

    # now handle circular refs for non-atomic objects
    if oid in seen:
        ref = seen[oid]
        print(f"{prefix}{name_col} ({type_col}): <circular ref to {ref}>")
        return
    seen[oid] = name

    shallow = getsizeof(obj)
    try:
        pickled = len(dill.dumps(obj, recurse=True, byref=False))  # type: ignore
    except Exception:
        pickled = -1
    size_info = f"shallow={shallow}B" + (f", pickled={pickled}B" if pickled >= 0 else "")

    # atomic
    if is_atomic(obj):
        print(f"{prefix}{name_col} ({type_col}, {size_info}): {repr(obj)}")
        return

    # composite
    print(f"{prefix}{name_col} ({type_col}, {size_info}):")
    if isinstance(obj, dict):
        items: List[Any] = list(obj.items())  # type: ignore
        for idx, (k, v) in enumerate(items):
            last = idx == len(items) - 1
            inspect_obj(v, f"{name}[{repr(k)}]", markers + [not last], seen, last)
    elif isinstance(obj, (list, tuple, set)):
        seq: List[Any] = list(obj)  # type: ignore
        for idx, v in enumerate(seq):
            last = idx == len(seq) - 1
            inspect_obj(v, f"{name}[{idx}]", markers + [not last], seen, last)
    else:
        try:
            attrs: Dict[str, Any] = vars(obj)  # type: ignore
        except TypeError:
            print(f"{prefix}    <no __dict__>: {repr(obj)}")
        else:
            items: List[Any] = list(attrs.items())  # type: ignore
            for idx, (attr, val) in enumerate(items):
                last = idx == len(items) - 1
                inspect_obj(val, f"{name}.{attr}", markers + [not last], seen, last)


def load_data(path: str) -> Any:
    if len(path) == 32 and "/" not in path:
        path = uuid_path.format(uuid=path)
    elif "/" not in path:
        path = direct_path.format(name=path)
    data = gzip.open(path, "rb").read() if path.endswith(".gz") else open(path, "rb").read()
    return dill.loads(data)  # type: ignore


def collect_stats(obj: Any) -> Dict[str, Any]:
    seen: Set[int] = set()
    stats: Dict[str, Any] = {"total_nodes": 0, "total_size": 0, "type_counts": {}, "ref_counts": {}, "size_map": {}}

    def _rec(object_reference: Any, path: str = "root") -> None:
        oid = id(object_reference)
        stats["ref_counts"][oid] = stats["ref_counts"].get(oid, 0) + 1
        if oid in seen:
            return
        seen.add(oid)
        stats["total_nodes"] += 1
        size = getsizeof(object_reference)
        stats["total_size"] += size
        obj_type = type(object_reference).__name__
        stats["type_counts"][obj_type] = stats["type_counts"].get(obj_type, 0) + 1
        stats["size_map"][oid] = (path, obj_type, size)

        if is_atomic(object_reference):
            return
        if isinstance(object_reference, dict):
            for k, v in object_reference.items():  # type: ignore
                _rec(v, f"{path}[{repr(k)}]")  # type: ignore
        elif isinstance(object_reference, (list, tuple, set)):
            for i, v in enumerate(object_reference):  # type: ignore
                _rec(v, f"{path}[{i}]")
        else:
            try:
                for k, v in vars(object_reference).items():  # type: ignore
                    _rec(v, f"{path}.{k}")
            except Exception:
                return

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
    # Basic stats
    print("Object graph stats:")
    print(f"  total nodes visited: {stats['total_nodes']}")
    print(f"  total shallow size: {stats['total_size']} bytes")
    print(f"  distinct types: {len(stats['type_counts'])}")

    # Top types
    print("  top types:")
    for t, c in sorted(stats["type_counts"].items(), key=lambda x: -x[1])[:5]:
        print(f"    {t}: {c}")
    print()

    # Biggest objects by size
    print("Biggest objects (by shallow size):")
    biggest = sorted(stats["size_map"].values(), key=lambda x: -x[2])[:5]
    for path, typ, sz in biggest:
        print(f"  {path} ({typ}): {sz} bytes")
    print()

    # Top referenced objects
    print("Most referenced objects (multiple pointers):")
    refs = [(oid, cnt) for oid, cnt in stats["ref_counts"].items() if cnt > 1]
    refs_sorted = sorted(refs, key=lambda x: -x[1])[:5]
    for oid, cnt in refs_sorted:
        path, typ, sz = stats["size_map"].get(oid, ("<unknown>", type, 0))
        print(f"  {path} ({typ}): referenced {cnt} times, size {sz} bytes")


def save_inspect(path: str) -> None:
    data = load_data(path)
    inspect_obj(data)


def capture_inspect(path: str) -> str:
    buf = StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        save_inspect(path)
    finally:
        sys.stdout = old
    return buf.getvalue()


def capture_subtree(obj: Any, path: str) -> str:
    buf = StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        inspect_obj(obj, name=path)
    finally:
        sys.stdout = old
    return buf.getvalue()


def find_matches(
    obj: Any, path: str, regex: re.Pattern[str], markers: Set[str], matches: List[Tuple[str, Any]]
) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():  # type: ignore
            new_path = f"{path}[{repr(k)}]"  # type: ignore
            if regex.fullmatch(new_path):
                matches.append((new_path, v))  # type: ignore
            find_matches(v, new_path, regex, markers, matches)
    elif isinstance(obj, (list, tuple, set)):
        for i, v in enumerate(obj):  # type: ignore
            new_path = f"{path}[{i}]"
            if regex.fullmatch(new_path):
                matches.append((new_path, v))  # type: ignore
            find_matches(v, new_path, regex, markers, matches)
    else:
        if regex.fullmatch(path):
            matches.append((path, obj))


if __name__ == "__main__":
    parser = ArgumentParser(description="Inspect a saved game dump, piping through $PAGER by default.")
    parser.add_argument("path", help="32-char UUID or save-name")
    parser.add_argument("--color", action="store_true", help="Enable ANSI coloring per type and level")
    parser.add_argument("--no-pager", action="store_true", help="Dump raw to stdout instead of paging")
    parser.add_argument("-q", "--query", help="Only display subtrees whose full path matches this regex")
    parser.add_argument(
        "--summary", action="store_true", help="Show a summary of the data (type counts, sizes, keys, biggest/refs)"
    )
    args = parser.parse_args()

    global COLOR_ENABLED
    COLOR_ENABLED = args.color or (sys.version_info >= (3, 13))
    if not args.path:
        print("No path provided.", file=sys.stderr)
        sys.exit(1)
    data = load_data(args.path)
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
        find_matches(data, "root", regex, set(), matches)  # type: ignore
        if not matches:
            print(f"No paths matched /{args.query}/", file=sys.stderr)
            sys.exit(1)
        parts = [capture_subtree(obj, path) for (path, obj) in matches]
        output = "\n".join(parts)
    else:
        buf = StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            inspect_obj(data)
        finally:
            sys.stdout = old
        output = buf.getvalue()
    if args.no_pager:
        sys.stdout.write(output)
    else:
        pydoc.pager(output)

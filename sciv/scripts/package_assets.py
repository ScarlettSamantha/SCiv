#!/usr/bin/env python3
import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathlib import Path
from typing import List, Optional, Set

from system.asset_archive import P3DAssetArchive


def _parse_exts(val: Optional[str]) -> Optional[Set[str]]:
    if not val:
        return None
    items: List[str] = [s.strip().lower() for s in val.replace(";", ",").split(",") if s.strip()]
    exts: Set[str] = set()
    for s in items:
        exts.add(s if s.startswith(".") else f".{s}")
    return exts


def _parse_paths(vals: List[str]) -> List[Path]:
    return [Path(v).resolve() for v in vals]


def main() -> int:
    p = argparse.ArgumentParser(prog="package_assets", add_help=True)
    p.add_argument("-i", "--input", action="append", required=False, default=["assets"])
    p.add_argument("-o", "--output", required=False, default="assets.mf")
    p.add_argument("--prefix", required=False, default="assets")
    p.add_argument("--mount-point", required=False, default="/")
    p.add_argument("-c", "--compression", type=int, required=False, default=6)
    p.add_argument("--include-exts", required=False, default=None, help="e.g. bam,png,jpg,ogg,glsl,kv,json,ttf,otf")
    p.add_argument("--exclude", action="append", default=[], help="glob, can repeat")
    p.add_argument("--force", action="store_true", default=False)
    p.add_argument("--mount", action="store_true", default=False)
    p.add_argument("--priority", type=int, default=0)
    p.add_argument("--list", action="store_true", default=False)
    args = p.parse_args()

    input_dirs: List[Path] = _parse_paths(args.input)
    output: Path = Path(args.output).resolve()
    include_exts: Set[str] | None = _parse_exts(args.include_exts)
    archive = P3DAssetArchive(
        input_dirs=input_dirs,
        archive_path=output,
        mount_point=args.mount_point,
        prefix=args.prefix,
        compression=args.compression,
        include_exts=include_exts,
        exclude_globs=args.exclude,
    )

    entries: List[str] = archive.list()

    print(f"wrote: {archive.archive_path}")
    print(f"manifest: {archive.archive_path.with_suffix(archive.archive_path.suffix + '.json')}")
    print(f"files: {len(entries)}")
    for entry in entries:
        print(f"  {entry}")

    if args.mount:
        print(f"mounted at: {args.mount_point} (priority {args.priority})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

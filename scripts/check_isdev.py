#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import importlib.util
import os


def main() -> int:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    version_path = os.path.join(script_dir, "../sciv/version.py")
    spec = importlib.util.spec_from_file_location("version", version_path)

    if spec is None:
        print(f"Error: Could not find version.py at {version_path}", file=sys.stderr)
        return 1

    version = importlib.util.module_from_spec(spec)

    if spec.loader is None:
        print(f"Error: Could not load version.py from {version_path}", file=sys.stderr)
        return 1

    spec.loader.exec_module(version)
    __isdev__ = version.__isdev__

    if __isdev__:
        print("❌  This is a development version of the package.", file=sys.stderr)
        return 1

    print("✅  This is a stable release of the package.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

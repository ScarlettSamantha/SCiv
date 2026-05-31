"""Compatibility launcher for the standalone SCiv worldgen viewer."""

from worldgen_viewer_tool.app import WorldgenViewerWindow, build_arg_parser, main

__all__ = ["WorldgenViewerWindow", "build_arg_parser", "main"]


if __name__ == "__main__":
    raise SystemExit(main())

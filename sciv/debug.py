#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess  # nosec B404
from pathlib import Path
from typing import Callable, Dict

from rich.console import Console


class DebugApp:
    def __init__(self):
        self.console = Console()
        self._actions: Dict[str, Callable[[argparse.Namespace], None]] = {
            "profile": self._profile,
            "clear-cache": self._clear_cache,
        }

    def _profile(self, args: argparse.Namespace) -> None:
        output = args.output_file
        cmd = f"py-spy record -t --format=speedscope -o {output} ./main.py"

        self.console.rule(f"[bold green]Profiling → {output}")
        self.console.print(f"[blue]Running:[/] {cmd}\n")
        try:
            subprocess.run(cmd, check=True, shell=True, env=os.environ.copy())  # nosec B602
        except subprocess.CalledProcessError as exc:
            self.console.print(f"[red]py-spy failed with exit code {exc.returncode}[/]")
        else:
            self.console.print(f"[bold green]Done![/] Profile saved to [underline]{output}[/]")

    def _clear_cache(self, args: argparse.Namespace) -> None:
        cache_dir = Path("assets/generated")
        if not cache_dir.exists():
            self.console.print(f"[yellow]No cache directory found at[/] {cache_dir}")
            return

        for item in cache_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        self.console.print(f"[bold green]Cache cleared in:[/] {cache_dir}")

    def run(self, args: argparse.Namespace) -> None:
        action = args.action
        if not action:
            self.console.print("[red]No action specified.[/]")
            return

        handler = self._actions.get(action)
        if not handler:
            self.console.print(f"[red]Unknown action:[/] {action}")
            return

        handler(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="debug.py",
        description="A small debug utility (profile, clear cache, etc.)",
    )

    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument(
        "--profile",
        dest="action",
        action="store_const",
        const="profile",
        help="Run py-spy to profile the application",
    )
    actions.add_argument(
        "--clear-cache",
        dest="action",
        action="store_const",
        const="clear-cache",
        help="Clear all files under assets/generated",
    )

    output_path_default = "./debugging/pyspy-stats.speedscope"
    os.makedirs(os.path.dirname(output_path_default), exist_ok=True)
    parser.add_argument(
        "-o",
        "--output-file",
        dest="output_file",
        default=output_path_default,
        help="Output file for profiling data (py-spy speedscope format)",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    app = DebugApp()
    app.run(args)


if __name__ == "__main__":
    main()

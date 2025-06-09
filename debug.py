#!/usr/bin/env python3
import argparse
import os
import subprocess
from rich.console import Console


class DebugApp:
    def __init__(self):
        self.console = Console()
        self._actions = {
            "profile": self._profile,
        }

    def _profile(self, args: argparse.Namespace):
        """
        Run py-spy to profile the target application.
        """
        output = args.output_file
        cmd = f"py-spy record -t --format=speedscope -o {output} ./main.py"

        self.console.rule(f"[bold green]Profiling → {output}")
        self.console.print(f"[blue]Running:[/] {cmd}\n")
        try:
            subprocess.run(cmd, check=True, shell=True, env=os.environ.copy())
        except subprocess.CalledProcessError as exc:
            self.console.print(f"[red]py-spy failed with exit code {exc.returncode}[/]")
        else:
            self.console.print(f"[bold green]Done![/] Profile saved to [underline]{output}[/]")

    def run(self, args: argparse.Namespace):
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
        description="A small debug utility (profile, benchmark, etc.)",
    )

    # Mutually exclusive actions
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument(
        "--profile", dest="action", action="store_const", const="profile", help="Run py-spy to profile the application"
    )

    output_path_default: str = "./debugging/pyspy-stats.speedscope"
    if not os.path.exists(os.path.dirname(output_path_default)):
        os.makedirs(os.path.dirname(output_path_default), exist_ok=True)

    parser.add_argument(
        "-o",
        "--output-file",
        dest="output_file",
        default="./debugging/pyspy-stats.speedscope",
        help="Output file for profiling data (py-spy speedscope format)",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    app = DebugApp()
    app.run(args)


if __name__ == "__main__":
    main()

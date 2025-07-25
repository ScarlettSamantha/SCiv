import os
import pathlib
import sys
from subprocess import run

from pyuac import main_requires_admin

requirements_command: str = (
    "python -m briefcase update --update-support --update-stub --update-resources --update-requirements"
)
build_command: str = "python -m briefcase build windows"
compile_command: str = "python -m briefcase package windows --adhoc-sign"


def cleanup_build():
    base = pathlib.Path(__file__).parent.parent / "build" / "sciv" / "windows" / "app" / "src" / "app" / "sciv"
    remove = [
        "assets/generated",
        "logs/",
        "saves/",
    ]
    for item in remove:
        path = base / item
        if path.exists():
            if path.is_dir():
                for sub_item in path.iterdir():
                    run(["del", "/F", "/Q", str(sub_item)], shell=True)
                run(["rmdir", "/S", "/Q", str(path)], shell=True)
                print(f"[Build-Cleanup]Removing {path}")
            else:
                run(["del", "/F", "/Q", str(path)], shell=True)
                print(f"[Build-Cleanup]Removing {path}")


@main_requires_admin(return_output=True)  # type: ignore
def main():
    project_root = pathlib.Path(__file__).parent.parent
    if not project_root.exists():
        print(f"Project root {project_root} does not exist.")
        sys.exit(1)

    os.chdir(project_root)

    print("Updating requirements...")
    result = run(requirements_command, shell=True)
    if result.returncode != 0:
        print("Failed to update requirements.")
        sys.exit(result.returncode)

    print("Building the application...")
    result = run(build_command, shell=True)
    if result.returncode != 0:
        print("Failed to build the application.")
        sys.exit(result.returncode)

    cleanup_build()

    print("Compiling the application...")
    result = run(compile_command, shell=True)
    if result.returncode != 0:
        print("Failed to compile the application.")
        sys.exit(result.returncode)

    print("Build process completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    instance = main()
    if instance:
        admin_stdout_str, admin_stderr_str, *_ = instance  # type: ignore
        if admin_stdout_str:
            print(admin_stdout_str)  # type: ignore
        if admin_stderr_str:
            print(admin_stderr_str)  # type: ignore

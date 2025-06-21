from subprocess import run
import pathlib
import sys
import os
import ctypes
import pyuac

requirements_command: str = "python -m briefcase update -r"
build_command: str = "python -m briefcase build"
compile_command: str = "python -m briefcase package"


def is_admin() -> bool:
    try:
        return os.getuid() == 0
    except AttributeError:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore


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
                    sub_item.unlink(missing_ok=True)
                path.rmdir()
                print(f"[Build-Cleanup]Removing {path}")
            else:
                path.unlink(missing_ok=True)


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
    if not pyuac.isUserAdmin():
        print("Re-launching as admin!")
        pyuac.runAsAdmin()  # type: ignore
    else:
        main()

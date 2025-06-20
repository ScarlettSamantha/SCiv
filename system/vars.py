from typing import List, Tuple, Optional

from version import __major__, __minor__, __patch__, __version__, __version_name__

VERSION_MAJOR: int = __major__
VERSION_MINOR: int = __minor__
VERSION_PATCH: int = __patch__
VERSION: str = __version__
VERSION_NAME: str = __version_name__
VERSION_NAME_STRING: str = f"{VERSION}-{VERSION_NAME}"

# Meta information
APPLICATION_TYPE: str = "Game"
APPLICATION_NAME: str = "SCIV"

CREATOR: Tuple[str, str] = ("Scarlett Samantha Verheul", "scarlett.verheul@gmail.com")
REPOSITORY: str = "https://git.scarlettbytes.nl/scarlett/panda-openciv"

AUTHORS: List[Tuple[str, str]] = [CREATOR]

DEBUG: bool = True
commit: Optional[str] = None


def get_git_commit() -> str:
    from system.vars import commit

    if commit is None:
        try:
            import git  # type: ignore

            repo = git.Repo(search_parent_directories=True)  # type: ignore
            commit = str(repo.head.object.hexsha)  # type: ignore
        except Exception:
            commit = "Unknown"
    return commit

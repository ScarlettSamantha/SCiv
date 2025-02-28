from typing import List, Tuple

VERSION_MAJOR: int = 0
VERSION_MINOR: int = 1
VERSION_PATCH: int = 0
VERSION: Tuple[int, int, int] = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
VERSION_NAME: str = "Alpha"
VERSION_STRING: str = ".".join(str(i) for i in VERSION)
VERSION_NAME_STRING: str = f"{VERSION_STRING}-{VERSION_NAME}"

# Meta information
APPLICATION_TYPE: str = "Game"
APPLICATION_NAME: str = "SCIV"

CREATOR: Tuple[str, str] = ("Scarlett Samantha Verheul", "scarlett.verheul@gmail.com")

AUTHORS: List[Tuple[str, str]] = [CREATOR]


class Colors:
    RESTORE = (1, 1, 1, 1)

    RED = (1, 0, 0, 1)
    GREEN = (0, 1, 0, 1)
    BLUE = (0, 0, 1, 1)
    TIEL = (0.5, 0.2, 0.7, 1)
    YELLOW = (1, 1, 0, 1)
    BLACK = (0, 0, 0, 1)
    ORANGE = (1, 0.5, 0, 1)
    PURPLE = (0.5, 0, 1, 1)
    GREY = (0.5, 0.5, 0.5, 1)

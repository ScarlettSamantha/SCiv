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

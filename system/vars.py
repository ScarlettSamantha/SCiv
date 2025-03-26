from typing import List, Tuple

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

AUTHORS: List[Tuple[str, str]] = [CREATOR]

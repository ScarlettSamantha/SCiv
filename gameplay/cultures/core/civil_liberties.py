from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class CivilLiberties(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.civil_liberties",
            name=t_("content.culture.civics.core.civil_liberties.name"),
            description=t_("content.culture.civics.core.civil_liberties.description"),
            *args,
            **kwargs,
        )

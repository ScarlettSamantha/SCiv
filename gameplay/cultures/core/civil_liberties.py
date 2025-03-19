from gameplay.culture import Civic
from managers.i18n import _t


class CivilLiberties(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.civil_liberties",
            name=_t("content.culture.civics.core.civil_liberties.name"),
            description=_t("content.culture.civics.core.civil_liberties.description"),
            *args,
            **kwargs,
        )

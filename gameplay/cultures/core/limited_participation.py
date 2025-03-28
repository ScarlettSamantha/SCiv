from gameplay.culture import Civic
from managers.i18n import _t


class LimitedParticipation(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.limited_participation",
            name=_t("content.culture.civics.core.limited_participation.name"),
            description=_t("content.culture.civics.core.limited_participation.description"),
            *args,
            **kwargs,
        )

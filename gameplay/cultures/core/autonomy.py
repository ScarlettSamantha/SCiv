from gameplay.culture import Civic
from managers.i18n import _t


class Autonomy(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.autonomy",
            name=_t("content.culture.civics.core.autonomy.name"),
            description=_t("content.culture.civics.core.autonomy.description"),
            *args,
            **kwargs,
        )

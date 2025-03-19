from gameplay.culture import Civic
from managers.i18n import _t


class Decentralization(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.decentralization",
            name=_t("content.culture.civics.core.decentralization.name"),
            description=_t("content.culture.civics.core.decentralization.description"),
            *args,
            **kwargs,
        )

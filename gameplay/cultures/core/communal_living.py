from gameplay.culture import Civic
from managers.i18n import _t


class CommunalLiving(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.communal_living",
            name=_t("content.culture.civics.core.communal_living.name"),
            description=_t("content.culture.civics.core.communal_living.description"),
            *args,
            **kwargs,
        )

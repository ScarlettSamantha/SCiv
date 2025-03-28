from gameplay.culture import Civic
from managers.i18n import _t


class FreeMarket(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.free_market",
            name=_t("content.culture.civics.core.free_market.name"),
            description=_t("content.culture.civics.core.free_market.description"),
            *args,
            **kwargs,
        )

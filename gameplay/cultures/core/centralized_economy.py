from gameplay.culture import Civic
from managers.i18n import _t


class CentralizedEconomy(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.centralized_economy",
            name=_t("content.culture.civics.core.centralized_economy.name"),
            description=_t("content.culture.civics.core.centralized_economy.description"),
            *args,
            **kwargs,
        )

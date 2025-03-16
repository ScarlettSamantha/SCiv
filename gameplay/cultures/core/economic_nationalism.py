from gameplay.culture import Civic
from managers.i18n import _t


class EconomicNationalism(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.economic_nationalism",
            name=_t("content.culture.civics.core.economic_nationalism.name"),
            description=_t("content.culture.civics.core.economic_nationalism.description"),
            *args,
            **kwargs,
        )

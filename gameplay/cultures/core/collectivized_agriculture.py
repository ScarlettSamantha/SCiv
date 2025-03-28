from gameplay.culture import Civic
from managers.i18n import _t


class CollectivizedAgriculture(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.collectivized_agriculture",
            name=_t("content.culture.civics.core.collectivized_agriculture.name"),
            description=_t("content.culture.civics.core.collectivized_agriculture.description"),
            *args,
            **kwargs,
        )

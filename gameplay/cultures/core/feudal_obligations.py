from gameplay.culture import Civic
from managers.i18n import _t


class FeudalObligations(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.feudal_obligations",
            name=_t("content.culture.civics.core.feudal_obligations.name"),
            description=_t("content.culture.civics.core.feudal_obligations.description"),
            *args,
            **kwargs,
        )

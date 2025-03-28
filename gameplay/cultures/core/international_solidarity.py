from gameplay.culture import Civic
from managers.i18n import _t


class InternationalSolidarity(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.international_solidarity",
            name=_t("content.culture.civics.core.international_solidarity.name"),
            description=_t("content.culture.civics.core.international_solidarity.description"),
            *args,
            **kwargs,
        )

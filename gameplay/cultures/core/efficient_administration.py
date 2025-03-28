from gameplay.culture import Civic
from managers.i18n import _t


class EfficientAdministration(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.efficient_administration",
            name=_t("content.culture.civics.core.efficient_administration.name"),
            description=_t("content.culture.civics.core.efficient_administration.description"),
            *args,
            **kwargs,
        )

from gameplay.culture import Civic
from managers.i18n import _t


class MoralLegislation(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.moral_legislation",
            name=_t("content.culture.civics.core.moral_legislation.name"),
            description=_t("content.culture.civics.core.moral_legislation.description"),
            *args,
            **kwargs,
        )

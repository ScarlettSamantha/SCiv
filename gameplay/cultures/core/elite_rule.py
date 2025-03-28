from gameplay.culture import Civic
from managers.i18n import _t


class EliteRule(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.elite_rule",
            name=_t("content.culture.civics.core.elite_rule.name"),
            description=_t("content.culture.civics.core.elite_rule.description"),
            *args,
            **kwargs,
        )

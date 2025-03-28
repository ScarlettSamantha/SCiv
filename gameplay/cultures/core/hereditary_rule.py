from gameplay.culture import Civic
from managers.i18n import _t


class HereditaryRule(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.hereditary_rule",
            name=_t("content.culture.civics.core.hereditary_rule.name"),
            description=_t("content.culture.civics.core.hereditary_rule.description"),
            *args,
            **kwargs,
        )

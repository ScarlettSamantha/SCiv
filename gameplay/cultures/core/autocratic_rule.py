from __future__ import annotations
from gameplay.culture import Civic
from managers.i18n import _t


class AutocraticRule(Civic):
    def __init__(self, *args, **kwargs):
        super().__init__(
            key="core.culture.civics.autocratic_rule",
            name=_t("content.culture.civics.core.autocratic_rule.name"),
            description=_t("content.culture.civics.core.autocratic_rule.description"),
            *args,
            **kwargs,
        )

from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class AutocraticRule(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.autocratic_rule",
            name=t_("content.culture.civics.core.autocratic_rule.name"),
            description=t_("content.culture.civics.core.autocratic_rule.description"),
            *args,
            **kwargs,
        )

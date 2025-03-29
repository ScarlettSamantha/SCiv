from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class EliteRule(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.elite_rule",
            name=t_("content.culture.civics.core.elite_rule.name"),
            description=t_("content.culture.civics.core.elite_rule.description"),
            *args,
            **kwargs,
        )

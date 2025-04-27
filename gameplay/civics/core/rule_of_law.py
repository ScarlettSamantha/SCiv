from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class RuleOfLaw(Civic):
    key = "core.culture.civics.rule_of_law"
    name = t_("content.culture.civics.core.rule_of_law.name")
    description = t_("content.culture.civics.core.rule_of_law.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

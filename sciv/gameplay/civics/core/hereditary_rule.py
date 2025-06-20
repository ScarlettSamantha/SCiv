from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class HereditaryRule(Civic):
    key = "core.culture.civics.hereditary_rule"
    name = t_("content.culture.civics.core.hereditary_rule.name")
    description = t_("content.culture.civics.core.hereditary_rule.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

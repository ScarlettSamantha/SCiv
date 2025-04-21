from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class DivineGovernance(Civic):
    key = "core.culture.civics.divine_governance"
    name = t_("content.culture.civics.core.divine_governance.name")
    description = t_("content.culture.civics.core.divine_governance.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

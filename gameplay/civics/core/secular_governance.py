from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class SecularGovernance(Civic):
    key = "core.culture.civics.secular_governance"
    name = t_("content.culture.civics.core.secular_governance.name")
    description = t_("content.culture.civics.core.secular_governance.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

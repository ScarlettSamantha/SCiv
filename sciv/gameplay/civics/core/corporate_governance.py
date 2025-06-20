from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class CorporateGovernance(Civic):
    key = "core.culture.civics.corporate_governance"
    name = t_("content.culture.civics.core.corporate_governance.name")
    description = t_("content.culture.civics.core.corporate_governance.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class CorporateGovernance(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.corporate_governance",
            name=t_("content.culture.civics.core.corporate_governance.name"),
            description=t_("content.culture.civics.core.corporate_governance.description"),
            *args,
            **kwargs,
        )

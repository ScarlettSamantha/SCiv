from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class SecularGovernance(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.secular_governance",
            name=t_("content.culture.civics.core.secular_governance.name"),
            description=t_("content.culture.civics.core.secular_governance.description"),
            *args,
            **kwargs,
        )

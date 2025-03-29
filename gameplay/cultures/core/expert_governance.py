from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class ExpertGovernance(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.expert_governance",
            name=t_("content.culture.civics.core.expert_governance.name"),
            description=t_("content.culture.civics.core.expert_governance.description"),
            *args,
            **kwargs,
        )

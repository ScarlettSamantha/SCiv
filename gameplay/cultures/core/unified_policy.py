from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class UnifiedPolicy(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.unified_policy",
            name=t_("content.culture.civics.core.unified_policy.name"),
            description=t_("content.culture.civics.core.unified_policy.description"),
            *args,
            **kwargs,
        )

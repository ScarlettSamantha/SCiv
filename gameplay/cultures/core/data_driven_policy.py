from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class DataDrivenPolicy(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.data_driven_policy",
            name=t_("content.culture.civics.core.data_driven_policy.name"),
            description=t_("content.culture.civics.core.data_driven_policy.description"),
            *args,
            **kwargs,
        )

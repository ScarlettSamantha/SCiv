from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class DataDrivenPolicy(Civic):
    key = "core.culture.civics.data_driven_policy"
    name = t_("content.culture.civics.core.data_driven_policy.name")
    description = t_("content.culture.civics.core.data_driven_policy.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

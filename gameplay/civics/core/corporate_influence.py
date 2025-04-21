from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class CorporateInfluence(Civic):
    key = "core.culture.civics.corporate_influence"
    name = t_("content.culture.civics.core.corporate_influence.name")
    description = t_("content.culture.civics.core.corporate_influence.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

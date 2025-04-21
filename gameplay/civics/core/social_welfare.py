from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class SocialWelfare(Civic):
    key = "core.culture.civics.social_welfare"
    name = t_("content.culture.civics.core.social_welfare.name")
    description = t_("content.culture.civics.core.social_welfare.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

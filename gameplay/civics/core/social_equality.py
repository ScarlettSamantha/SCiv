from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class SocialEquality(Civic):
    key = "core.culture.civics.social_equality"
    name = t_("content.culture.civics.core.social_equality.name")
    description = t_("content.culture.civics.core.social_equality.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

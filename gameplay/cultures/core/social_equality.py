from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class SocialEquality(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.social_equality",
            name=t_("content.culture.civics.core.social_equality.name"),
            description=t_("content.culture.civics.core.social_equality.description"),
            *args,
            **kwargs,
        )

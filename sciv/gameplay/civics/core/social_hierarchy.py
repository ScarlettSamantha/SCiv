from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class SocialHierarchy(Civic):
    key = "core.culture.civics.social_hierarchy"
    name = t_("content.culture.civics.core.social_hierarchy.name")
    description = t_("content.culture.civics.core.social_hierarchy.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

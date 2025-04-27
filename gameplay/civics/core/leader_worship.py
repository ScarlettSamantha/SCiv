from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class LeaderWorship(Civic):
    key = "core.culture.civics.leader_worship"
    name = t_("content.culture.civics.core.leader_worship.name")
    description = t_("content.culture.civics.core.leader_worship.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

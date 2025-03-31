from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class LeaderWorship(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.leader_worship",
            name=t_("content.culture.civics.core.leader_worship.name"),
            description=t_("content.culture.civics.core.leader_worship.description"),
            *args,
            **kwargs,
        )

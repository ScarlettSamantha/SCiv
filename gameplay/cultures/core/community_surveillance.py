from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class CommunitySurveillance(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.community_surveillance",
            name=t_("content.culture.civics.core.community_surveillance.name"),
            description=t_("content.culture.civics.core.community_surveillance.description"),
            *args,
            **kwargs,
        )

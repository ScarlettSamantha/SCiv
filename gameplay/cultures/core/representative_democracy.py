from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class RepresentativeDemocracy(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.representative_democracy",
            name=t_("content.culture.civics.core.representative_democracy.name"),
            description=t_("content.culture.civics.core.representative_democracy.description"),
            *args,
            **kwargs,
        )

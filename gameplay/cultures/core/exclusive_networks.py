from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class ExclusiveNetworks(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.exclusive_networks",
            name=t_("content.culture.civics.core.exclusive_networks.name"),
            description=t_("content.culture.civics.core.exclusive_networks.description"),
            *args,
            **kwargs,
        )

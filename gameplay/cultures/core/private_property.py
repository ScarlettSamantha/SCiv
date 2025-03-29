from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class PrivateProperty(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.private_property",
            name=t_("content.culture.civics.core.private_property.name"),
            description=t_("content.culture.civics.core.private_property.description"),
            *args,
            **kwargs,
        )

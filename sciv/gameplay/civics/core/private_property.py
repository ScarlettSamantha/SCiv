from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class PrivateProperty(Civic):
    key = "core.culture.civics.private_property"
    name = t_("content.culture.civics.core.private_property.name")
    description = t_("content.culture.civics.core.private_property.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

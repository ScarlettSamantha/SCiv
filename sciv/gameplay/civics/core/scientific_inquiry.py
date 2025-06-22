from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class ScientificInquiry(Civic):
    key = "core.culture.civics.scientific_inquiry"
    name = t_("content.culture.civics.core.scientific_inquiry.name")
    description = t_("content.culture.civics.core.scientific_inquiry.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

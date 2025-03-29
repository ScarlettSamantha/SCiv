from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class ScientificInquiry(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.scientific_inquiry",
            name=t_("content.culture.civics.core.scientific_inquiry.name"),
            description=t_("content.culture.civics.core.scientific_inquiry.description"),
            *args,
            **kwargs,
        )

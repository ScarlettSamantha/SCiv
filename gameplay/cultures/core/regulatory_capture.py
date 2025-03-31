from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class RegulatoryCapture(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.regulatory_capture",
            name=t_("content.culture.civics.core.regulatory_capture.name"),
            description=t_("content.culture.civics.core.regulatory_capture.description"),
            *args,
            **kwargs,
        )

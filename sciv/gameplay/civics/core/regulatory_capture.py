from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class RegulatoryCapture(Civic):
    key = "core.culture.civics.regulatory_capture"
    name = t_("content.culture.civics.core.regulatory_capture.name")
    description = t_("content.culture.civics.core.regulatory_capture.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

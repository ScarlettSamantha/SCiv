from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class SeperationChurchState(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.secularism",
            name=t_("content.culture.civics.core.secularism.name"),
            description=t_("content.culture.civics.core.secularism.description"),
            *args,
            **kwargs,
        )

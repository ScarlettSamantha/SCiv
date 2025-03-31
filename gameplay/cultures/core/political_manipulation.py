from typing import Any

from gameplay.culture import Civic
from managers.i18n import t_


class PoliticalManipulation(Civic):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            key="core.culture.civics.political_manipulation",
            name=t_("content.culture.civics.core.political_manipulation.name"),
            description=t_("content.culture.civics.core.political_manipulation.description"),
            *args,
            **kwargs,
        )

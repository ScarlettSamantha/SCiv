from typing import Any

from gameplay.civic import Civic
from managers.i18n import t_


class MarketCompetition(Civic):
    key = "core.culture.civics.market_competition"
    name = t_("content.culture.civics.core.market_competition.name")
    description = t_("content.culture.civics.core.market_competition.description")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class Willem(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.willem",
            name=t_("civilization.low_countries.leaders.willem.name"),
            description=t_("civilization.low_countries.leaders.willem.description"),
            icon="civilization/low_countries/leaders/willem/leader_icon.png",
        )
        self._effects = Effects()

from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class Ambiorix(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.ambiorix",
            name=t_("civilization.low_countries.leaders.ambiorix.name"),
            description=t_("civilization.low_countries.leaders.ambiorix.description"),
            icon="civilization/low_countries/leaders/ambiorix/leader_icon.png",
        )
        self._effects = Effects()

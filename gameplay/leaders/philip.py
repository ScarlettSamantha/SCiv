from __future__ import annotations

from gameplay.effect import Effects
from gameplay.leader import Leader
from managers.i18n import t_


class Philip(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.philip",
            name=t_("civilization.spain.leaders.philip.name"),
            description=t_("civilization.spain.leaders.philip.description"),
            icon="civilization/spain/leaders/philip/leader_icon.png",
        )
        self._effects = Effects()

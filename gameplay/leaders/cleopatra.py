from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class Cleopatra(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.cleopatra",
            name=t_("civilization.egypte.leaders.cleopatra.name"),
            description=t_("civilization.egypte.leaders.cleopatra.description"),
            icon="civilization/egypte/leaders/cleopatra/leader_icon.png",
        )
        self._effects = Effects()

from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class Kamehameha(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.kamehameha",
            name=t_("civilization.american_empire.leaders.kamehameha.name"),
            description=t_("civilization.american_empire.leaders.kamehameha.description"),
            icon="civilization/american_empire/leaders/kamehameha/leader_icon.png",
        )
        self._effects = Effects()

from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class Louis(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.louis",
            name=t_("civilization.france.leaders.louis.name"),
            description=t_("civilization.france.leaders.louis.description"),
            icon="civilization/france/leaders/louis/leader_icon.png",
        )
        self._effects = Effects()

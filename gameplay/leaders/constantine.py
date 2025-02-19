from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class Constantine(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.constantine",
            name=t_("civilization.byzantine.leaders.constantine.name"),
            description=t_("civilization.byzantine.leaders.constantine.description"),
            icon="civilization/byzantine/leaders/constantine/leader_icon.png",
        )
        self._effects = Effects()

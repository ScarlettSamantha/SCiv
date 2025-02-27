from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class Justinian(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.justinian",
            name=t_("civilization.byzantine.leaders.justinian.name"),
            description=t_("civilization.byzantine.leaders.justinian.description"),
            icon="civilization/byzantine/leaders/justinian/leader_icon.png",
        )
        self._effects = Effects()

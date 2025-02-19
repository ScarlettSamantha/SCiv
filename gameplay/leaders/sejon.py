from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class Sejon(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.sejoin",
            name=t_("civilization.korea.leaders.sejoin.name"),
            description=t_("civilization.korea.leaders.sejoin.description"),
            icon="civilization/korea/leaders/sejoin/leader_icon.png",
        )
        self._effects = Effects()

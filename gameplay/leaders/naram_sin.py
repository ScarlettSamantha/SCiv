from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class NaramSin(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.naram_sin",
            name=t_("civilization.akkadian.leaders.naram_sin.name"),
            description=t_("civilization.akkadian.leaders.naram_sin.description"),
            icon="civilization/akkadian/leaders/naram_sin/leader_icon.png",
        )
        self._effects = Effects()

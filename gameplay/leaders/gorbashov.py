from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class Gorbashov(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.gorbashov",
            name=t_("civilization.ussr.leaders.gorbashov.name"),
            description=t_("civilization.ussr.leaders.gorbashov.description"),
            icon="civilization/ussr/leaders/gorbashov/leader_icon.png",
        )
        self._effects = Effects()

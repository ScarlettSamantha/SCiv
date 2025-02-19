from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class Elizabeth(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.elizabeth",
            name=t_("civilization.england.leaders.elizabeth.name"),
            description=t_("civilization.england.leaders.elizabeth.description"),
            icon="civilization/england/leaders/elizabeth/leader_icon.png",
        )
        self._effects = Effects()

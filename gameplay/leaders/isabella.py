from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class Isabella(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.isabella",
            name=t_("civilization.spain.leaders.isabella.name"),
            description=t_("civilization.spain.leaders.isabella.description"),
            icon="civilization/spain/leaders/isabella/leader_icon.png",
        )
        self._effects = Effects()

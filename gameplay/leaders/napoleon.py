from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class Napoleon(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.napoleon",
            name=t_("civilization.france.leaders.napoleon.name"),
            description=t_("civilization.france.leaders.napoleon.description"),
            icon="civilization/france/leaders/napoleon/leader_icon.png",
        )
        self._effects = Effects()

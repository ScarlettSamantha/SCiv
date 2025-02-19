from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class FDR(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.fdr",
            name=t_("civilization.american_empire.leaders.fdr.name"),
            description=t_("civilization.american_empire.leaders.fdr.description"),
            icon="civilization/american_empire/leaders/fdr/leader_icon.png",
        )
        self._effects = Effects()

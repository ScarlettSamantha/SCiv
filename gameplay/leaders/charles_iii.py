from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class CharlesIII(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.charles_iii",
            name=t_("civilization.spain.leaders.charles_iii.name"),
            description=t_("civilization.spain.leaders.charles_iii.description"),
            icon="civilization/spain/leaders/charles_iii/leader_icon.png",
        )
        self._effects = Effects()

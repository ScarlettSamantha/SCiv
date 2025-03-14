from __future__ import annotations

from gameplay.effect import Effects
from gameplay.leader import Leader
from managers.i18n import t_


class Ramesses(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.ramesses",
            name=t_("civilization.egypt.leaders.ramesses.name"),
            description=t_("civilization.egypt.leaders.ramesses.description"),
            icon="civilization/egypt/leaders/ramesses/leader_icon.png",
        )
        self._effects = Effects()

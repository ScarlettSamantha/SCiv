from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class Tokugawa(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.tokugawa",
            name=t_("civilization.japan.leaders.tokugawa.name"),
            description=t_("civilization.japan.leaders.tokugawa.description"),
            icon="civilization/japan/leaders/tokugawa/leader_icon.png",
        )
        self._effects = Effects()

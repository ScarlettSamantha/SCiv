from __future__ import annotations

from gameplay.leader import Leader
from gameplay.effect import Effects
from managers.i18n import t_


class WuZetian(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.wu_zetian",
            name=t_("civilization.china.leaders.wu_zetian.name"),
            description=t_("civilization.china.leaders.wu_zetian.description"),
            icon="civilization/china/leaders/wu_zetian/leader_icon.png",
        )
        self._effects = Effects()

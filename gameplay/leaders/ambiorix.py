from gameplay.leader import Leader
from managers.i18n import t_


class Ambiorix(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.ambiorix",
            name=t_("civilization.netherlands.leaders.ambiorix.name"),
            description=t_("civilization.netherlands.leaders.ambiorix.description"),
            icon="civilization/netherlands/leaders/ambiorix/leader_icon.png",
        )

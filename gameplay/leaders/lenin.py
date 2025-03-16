from gameplay.leader import Leader
from managers.i18n import t_


class Lenin(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.lenin",
            name=t_("civilization.ussr.leaders.lenin.name"),
            description=t_("civilization.ussr.leaders.lenin.description"),
            icon="civilization/ussr/leaders/lenin/leader_icon.png",
        )

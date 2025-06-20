from gameplay.leader import Leader
from managers.i18n import t_


class Cnut(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.cnut",
            name=t_("civilization.vikings.leaders.cnut.name"),
            description=t_("civilization.vikings.leaders.cnut.description"),
            icon="civilization/vikings/leaders/cnut/leader_icon.png",
        )

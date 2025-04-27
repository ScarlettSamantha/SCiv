from gameplay.leader import Leader
from managers.i18n import t_


class Boiorix(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.boiorix",
            name=t_("civilization.barbarians.leaders.boiorix.name"),
            description=t_("civilization.barbarians.leaders.boiorix.description"),
            icon="civilization/barbarians/leaders/boiorix/leader_icon.png",
        )

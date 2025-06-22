from gameplay.leader import Leader
from managers.i18n import t_


class Gaiseric(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.gaiseric",
            name=t_("civilization.barbarians.leaders.gaiseric.name"),
            description=t_("civilization.barbarians.leaders.gaiseric.description"),
            icon="civilization/barbarians/leaders/gaiseric/leader_icon.png",
        )

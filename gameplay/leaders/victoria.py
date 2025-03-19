from gameplay.leader import Leader
from managers.i18n import t_


class Victoria(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.victoria",
            name=t_("civilization.england.leaders.victoria.name"),
            description=t_("civilization.england.leaders.victoria.description"),
            icon="civilization/england/leaders/victoria/leader_icon.png",
        )

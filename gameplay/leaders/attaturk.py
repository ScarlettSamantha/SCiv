from gameplay.leader import Leader
from managers.i18n import t_


class Attaturk(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.attaturk",
            name=t_("civilization.ottoman.leaders.attaturk.name"),
            description=t_("civilization.ottoman.leaders.attaturk.description"),
            icon="civilization/ottoman/leaders/attaturk/leader_icon.png",
        )

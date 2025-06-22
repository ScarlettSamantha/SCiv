from gameplay.leader import Leader
from managers.i18n import t_


class Alboin(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.alboin",
            name=t_("civilization.barbarians.leaders.alboin.name"),
            description=t_("civilization.barbarians.leaders.alboin.description"),
            icon="civilization/barbarians/leaders/alboin/leader_icon.png",
        )

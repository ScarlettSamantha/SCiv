from gameplay.leader import Leader
from managers.i18n import t_


class Boudicca(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.boudicca",
            name=t_("civilization.barbarians.leaders.boudicca.name"),
            description=t_("civilization.barbarians.leaders.boudicca.description"),
            icon="civilization/barbarians/leaders/boudicca/leader_icon.png",
        )

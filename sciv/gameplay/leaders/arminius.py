from gameplay.leader import Leader
from managers.i18n import t_


class Arminius(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.arminius",
            name=t_("civilization.barbarians.leaders.arminius.name"),
            description=t_("civilization.barbarians.leaders.arminius.description"),
            icon="civilization/barbarians/leaders/arminius/leader_icon.png",
        )

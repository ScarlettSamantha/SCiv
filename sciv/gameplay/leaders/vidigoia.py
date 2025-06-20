from gameplay.leader import Leader
from managers.i18n import t_


class Vidigoia(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.vidigoia",
            name=t_("civilization.barbarians.leaders.vidigoia.name"),
            description=t_("civilization.barbarians.leaders.vidigoia.description"),
            icon="civilization/barbarians/leaders/vidigoia/leader_icon.png",
        )

from gameplay.leader import Leader
from managers.i18n import t_


class Ceasar(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.ceasar",
            name=t_("civilization.rome.leaders.ceasar.name"),
            description=t_("civilization.rome.leaders.ceasar.description"),
            icon="civilization/rome/leaders/ceasar/leader_icon.png",
        )

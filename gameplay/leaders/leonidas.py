from gameplay.leader import Leader
from managers.i18n import t_


class Leonidas(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.leonidas",
            name=t_("civilization.greece.leaders.leonidas.name"),
            description=t_("civilization.greece.leaders.leonidas.description"),
            icon="civilization/greece/leaders/leonidas/leader_icon.png",
        )

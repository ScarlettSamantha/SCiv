from gameplay.leader import Leader
from managers.i18n import t_


class Alexander(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.alexander",
            name=t_("civilization.greece.leaders.alexander.name"),
            description=t_("civilization.greece.leaders.alexander.description"),
            icon="civilization/greece/leaders/alexander/leader_icon.png",
        )

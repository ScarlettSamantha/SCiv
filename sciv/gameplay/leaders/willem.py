from gameplay.leader import Leader
from managers.i18n import t_


class William(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.william",
            name=t_("civilization.netherlands.leaders.william.name"),
            description=t_("civilization.netherlands.leaders.william.description"),
            icon="civilization/netherlands/leaders/william/leader_icon.png",
        )

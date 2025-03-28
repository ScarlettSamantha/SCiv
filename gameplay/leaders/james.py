from gameplay.leader import Leader
from managers.i18n import t_


class James(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.james",
            name=t_("civilization.spain.leaders.james.name"),
            description=t_("civilization.spain.leaders.james.description"),
            icon="civilization/spain/leaders/james/leader_icon.png",
        )

from gameplay.leader import Leader
from managers.i18n import t_


class CharlesV(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.charles_v",
            name=t_("civilization.spain.leaders.charles_v.name"),
            description=t_("civilization.spain.leaders.charles_v.description"),
            icon="civilization/spain/leaders/charles_v/leader_icon.png",
        )

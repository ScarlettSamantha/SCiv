from gameplay.leader import Leader
from managers.i18n import t_


class William(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.william",
            name=t_("civilization.low_countries.leaders.william.name"),
            description=t_("civilization.low_countries.leaders.william.description"),
            icon="civilization/low_countries/leaders/william/leader_icon.png",
        )

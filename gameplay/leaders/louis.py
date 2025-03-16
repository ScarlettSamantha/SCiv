from gameplay.leader import Leader
from managers.i18n import t_


class Louis(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.louis",
            name=t_("civilization.france.leaders.louis.name"),
            description=t_("civilization.france.leaders.louis.description"),
            icon="civilization/france/leaders/louis/leader_icon.png",
        )

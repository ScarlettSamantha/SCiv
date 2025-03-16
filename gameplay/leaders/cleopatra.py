from gameplay.leader import Leader
from managers.i18n import t_


class Cleopatra(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.cleopatra",
            name=t_("civilization.egypt.leaders.cleopatra.name"),
            description=t_("civilization.egypt.leaders.cleopatra.description"),
            icon="civilization/egypt/leaders/cleopatra/leader_icon.png",
        )

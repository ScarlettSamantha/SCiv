from gameplay.leader import Leader
from managers.i18n import t_


class Darius(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.darius",
            name=t_("civilization.persia.leaders.darius.name"),
            description=t_("civilization.persia.leaders.darius.description"),
            icon="civilization/persia/leaders/darius/leader_icon.png",
        )

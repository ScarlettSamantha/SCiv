from gameplay.leader import Leader
from managers.i18n import t_


class Ragnar(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.ragnar",
            name=t_("civilization.vikings.leaders.ragnar.name"),
            description=t_("civilization.vikings.leaders.ragnar.description"),
            icon="civilization/vikings/leaders/ragnar/leader_icon.png",
        )

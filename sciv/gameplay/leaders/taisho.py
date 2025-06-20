from gameplay.leader import Leader
from managers.i18n import t_


class Taisho(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.taisho",
            name=t_("civilization.japan.leaders.taisho.name"),
            description=t_("civilization.japan.leaders.taisho.description"),
            icon="civilization/japan/leaders/taisho/leader_icon.png",
        )

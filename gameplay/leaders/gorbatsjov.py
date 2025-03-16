from gameplay.leader import Leader
from managers.i18n import t_


class Gorbatsjov(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.gorbatsjov",
            name=t_("civilization.ussr.leaders.gorbatsjov.name"),
            description=t_("civilization.ussr.leaders.gorbatsjov.description"),
            icon="civilization/ussr/leaders/gorbatsjov/leader_icon.png",
        )

from gameplay.leader import Leader
from managers.i18n import t_


class Sejong(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.sejong",
            name=t_("civilization.korea.leaders.sejong.name"),
            description=t_("civilization.korea.leaders.sejong.description"),
            icon="civilization/korea/leaders/sejong/leader_icon.png",
        )

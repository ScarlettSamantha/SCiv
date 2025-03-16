from gameplay.leader import Leader
from managers.i18n import t_


class Kublai(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.kublai",
            name=t_("civilization.china.leaders.kublai.name"),
            description=t_("civilization.china.leaders.kublai.description"),
            icon="civilization/china/leaders/kublai/leader_icon.png",
        )

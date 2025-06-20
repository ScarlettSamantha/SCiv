from gameplay.leader import Leader
from managers.i18n import t_


class Meiji(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.meiji",
            name=t_("civilization.japan.leaders.meiji.name"),
            description=t_("civilization.japan.leaders.meiji.description"),
            icon="civilization/japan/leaders/meiji/leader_icon.png",
        )

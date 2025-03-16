from gameplay.leader import Leader
from managers.i18n import t_


class AbrahamLincoln(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.abraham_lincoln",
            name=t_("civilization.american_empire.leaders.abraham_lincoln.name"),
            description=t_("civilization.american_empire.leaders.abraham_lincoln.description"),
            icon="civilization/american_empire/leaders/abraham_lincoln/leader_icon.png",
        )

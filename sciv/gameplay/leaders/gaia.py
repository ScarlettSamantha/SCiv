from gameplay.leader import Leader
from managers.i18n import t_


class Gaia(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.gaia",
            name=t_("civilization.nature.leaders.gaia.name"),
            description=t_("civilization.nature.leaders.gaia.description"),
            icon="civilization/nature/leaders/gaia/leader_icon.png",
        )

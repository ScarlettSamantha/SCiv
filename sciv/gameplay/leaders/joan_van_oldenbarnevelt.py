from gameplay.leader import Leader
from managers.i18n import t_


class JoanVanOldenbarnevelt(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.joan_van_oldenbarnevelt",
            name=t_("civilization.netherlands.leaders.joan_van_oldenbarnevelt.name"),
            description=t_("civilization.netherlands.leaders.joan_van_oldenbarnevelt.description"),
            icon="civilization/netherlands/leaders/joan_van_oldenbarnevelt/leader_icon.png",
        )

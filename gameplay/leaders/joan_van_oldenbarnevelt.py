from gameplay.leader import Leader
from managers.i18n import t_


class JoanVanOldenbarnevelt(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.joan_van_oldenbarnevelt",
            name=t_("civilization.low_countries.leaders.joan_van_oldenbarnevelt.name"),
            description=t_("civilization.low_countries.leaders.joan_van_oldenbarnevelt.description"),
            icon="civilization/low_countries/leaders/joan_van_oldenbarnevelt/leader_icon.png",
        )

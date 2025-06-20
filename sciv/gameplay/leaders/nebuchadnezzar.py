from gameplay.leader import Leader
from managers.i18n import t_


class Nebuchadnezzar(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.nebuchadnezzar",
            name=t_("civilization.persia.leaders.nebuchadnezzar.name"),
            description=t_("civilization.persia.leaders.nebuchadnezzar.description"),
            icon="civilization/persia/leaders/nebuchadnezzar/leader_icon.png",
        )

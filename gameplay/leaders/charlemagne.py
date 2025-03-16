from gameplay.leader import Leader
from managers.i18n import t_


class Charlemagne(Leader):
    def __init__(self) -> None:
        super().__init__(
            key="core.leaders.charlemange",
            name=t_("civilization.france.leaders.charlemange.name"),
            description=t_("civilization.france.leaders.charlemange.description"),
            icon="civilization/france/leaders/charlemange/leader_icon.png",
        )

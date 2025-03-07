from typing import TYPE_CHECKING

from gameplay.units.unit_base import UnitBaseClass
from managers.i18n import t_
from system.actions import Action

if TYPE_CHECKING:
    from gameplay.units.core.classes.civilian.settler import Settler


class FoundAction(Action):
    def __init__(self, instance: "UnitBaseClass | Settler"):
        super().__init__(
            name=t_("actions.unit.found_city"), action=instance.found_city, condition=instance.founding_conditions
        )
        self.on_the_spot_action = False
        self.targeting_tile_action = True
        self.get_return_as_failure_argument = True

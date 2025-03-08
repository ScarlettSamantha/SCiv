from typing import TYPE_CHECKING

from direct.showbase.MessengerGlobal import messenger

from gameplay.actions.unit.base_unit_action import BaseUnitAction
from gameplay.units.unit_base import UnitBaseClass
from managers.i18n import t_

if TYPE_CHECKING:
    from gameplay.units.core.classes.civilian.settler import Settler


class FoundAction(BaseUnitAction):
    def __init__(self, instance: "UnitBaseClass | Settler"):
        # Dynamically import Settler class to avoid circular import issues
        from gameplay.units.core.classes.civilian.settler import Settler

        if not isinstance(instance, Settler) and not issubclass(type(instance), Settler):
            raise TypeError("instance must be of type Settler or derivative")

        if isinstance(instance, UnitBaseClass) and not isinstance(
            instance, Settler
        ):  # This is a type hint, not a real check
            raise TypeError("instance must be of type Settler or derivative")

        self.unit: "Settler" = instance  # type: ignore # Properly reference Settler here

        super().__init__(
            name=t_("actions.unit.found_city"),
            action=self.found_action_wrapper,
            condition=instance.founding_conditions,  # type: ignore
            on_success=self.on_success,
        )

        self.on_the_spot_action = True
        self.targeting_tile_action = False

    def on_success(self, *args, **kwargs) -> bool:
        messenger.send("unit.action.found_city.success", [self.unit.tile])
        return True

    def found_action_wrapper(self, *args, **kwargs) -> bool:
        if not self.unit.tile.found(self.unit.owner):
            return False

        self.unit.destroy()
        return True

from typing import TYPE_CHECKING

from direct.showbase.MessengerGlobal import messenger

from gameplay.actions.unit.base_unit_action import BaseUnitAction
from gameplay.units.unit_base import UnitBaseClass
from managers.i18n import t_

if TYPE_CHECKING:
    from data.tiles.base_tile import BaseTile
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

        self.unit: "Settler" = instance
        self.tile: "BaseTile | None" = None

        super().__init__(
            name=t_("actions.unit.found_city"),
            action=self.found_action_wrapper,
            condition=instance.founding_conditions,  # type: ignore
            on_success=self.on_success,
        )

        self.on_the_spot_action = True
        self.targeting_tile_action = False

    def on_success(self, *args, **kwargs) -> bool:
        from managers.player import PlayerManager

        messenger.send("unit.action.found_city.success", [self.tile])

        if self.tile is None:
            raise AssertionError("Tile was not found")

        if self.tile.city is None:
            raise AssertionError("City was not founded")

        if (
            self.tile.owner == PlayerManager.player()
            and self.tile.city.player
            == PlayerManager.player()  # We check tile instead of unit as it should have been destroyed in the action. Which unregisters it from the player.
        ):  # check if the player is the owner of the unit/city
            if self.tile.city is not None and self.tile.city.is_capital:  # check if the city is a capital
                title, message = (
                    t_("ui.dialogs.unit.found_city.founded_own_capital.title"),
                    t_("ui.dialogs.unit.found_city.founded_own_capital.message"),
                )
            else:  # if not, it's a regular city
                title, message = (
                    t_("ui.dialogs.unit.found_city.city_founded.title"),
                    t_("ui.dialogs.unit.found_city.city_founded.message"),
                )
        else:
            title, message = (
                t_("ui.dialogs.unit.found_city.city_founded_by_other.title"),
                t_("ui.dialogs.unit.found_city.city_founded_by_other.message"),
            )

        messenger.send("ui.request.open.popup", ["city_founded", title, message])
        return True

    def found_action_wrapper(self, *args, **kwargs) -> bool:
        self.tile = self.unit.tile  # This has to be done before the unit is destroyed otherwise the tile will be None.
        if not self.unit.tile.found(self.unit.owner):
            return False

        self.unit.destroy()
        return True

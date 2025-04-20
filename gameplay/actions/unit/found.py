from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from direct.showbase.MessengerGlobal import messenger

from gameplay.actions.unit.base_unit_action import BaseUnitAction
from gameplay.repositories.tile import TileRepository
from gameplay.rules import GameRules
from helpers.cache import Cache
from managers.i18n import t_
from system.requires import Condition

if TYPE_CHECKING:
    from gameplay.tiles.base_tile import BaseTile
    from gameplay.units.core.classes.civilian.settler import Settler


CITY_FOUNDING_DISTANCE_RADIUS_DEFAULT: int = 2
CITY_FOUNDING_IN_OWN_TERRITORY_DEFAULT: bool = True


class CantFoundReasons(Enum):
    COULD_FOUND = 0
    TILE_IS_CITY = 1
    TILE_IS_OWNED = 2
    TILE_IS_NOT_PASSABLE = 3
    OTHER_CITY_TO_CLOSE = 4


class FoundAction(BaseUnitAction):
    def __init__(self, instance: "Settler"):
        # Dynamically import Settler class to avoid circular import issues

        super().__init__(
            name=t_("actions.unit.found_city"),
            action=self.found_action_wrapper,
            condition=self.founding_conditions,  # type: ignore
            on_success=self.on_success,  # type: ignore
            on_failure=self.on_failure,  # type: ignore
        )
        self.unit: "Settler" = instance
        self.tile: "BaseTile | None" = instance.get_tile()
        self.on_the_spot_action = True
        self.targeting_tile_action = False
        self.city_founding_distance_rule = CITY_FOUNDING_DISTANCE_RADIUS_DEFAULT
        self.city_founding_in_own_territory_rule = CITY_FOUNDING_IN_OWN_TERRITORY_DEFAULT

    def founding_conditions(self, _: Condition) -> bool:
        tile = self.unit.get_tile()
        base = Cache.get_showbase_instance()

        if tile is None:
            raise AssertionError("Tile was not found")

        rules: GameRules = base.game_manager_instance.rules  # type: ignore # We check above that the base instance is not None

        self.city_founding_distance_rule: int = rules.get_city_founding_distance_rule()
        self.city_founding_in_own_territory_rule: bool = rules.get_city_founding_in_own_territory_rule()

        if tile.player is None:  # if the tile is not owned by any player
            city_founding_in_own_territory_rule_implementation = True
        elif tile.player != self.unit.owner:  # if the tile is owned by another player
            city_founding_in_own_territory_rule_implementation = False
        elif tile.player == self.unit.owner:  # if the tile is owned by the player
            city_founding_in_own_territory_rule_implementation = (
                self.city_founding_in_own_territory_rule
            )  #  if the tile is owned by the player, check the rule
        else:  # Catch all
            city_founding_in_own_territory_rule_implementation = False

        if tile.is_city() is True:
            self.failure_reason = CantFoundReasons.TILE_IS_CITY
            return False
        elif city_founding_in_own_territory_rule_implementation is False:
            self.failure_reason = CantFoundReasons.TILE_IS_OWNED
            return False
        elif not tile.is_passable():
            self.failure_reason = CantFoundReasons.TILE_IS_NOT_PASSABLE
            return False
        elif len(TileRepository.get_cities_in_radius(tile, self.city_founding_distance_rule)) > 0:
            self.failure_reason = CantFoundReasons.OTHER_CITY_TO_CLOSE
            return False

        return True

    def on_failure(self, args: Tuple[Any], kwargs: Dict[Any, Any]) -> Optional[bool]:  # type: ignore
        if self.failure_reason == CantFoundReasons.TILE_IS_CITY:
            messenger.send(
                "ui.request.open.popup",
                [
                    "city_already_exists",
                    t_("ui.dialogs.unit.found_city.city_already_exists.title"),
                    t_("ui.dialogs.unit.found_city.city_already_exists.message"),
                ],
            )
        elif self.failure_reason == CantFoundReasons.TILE_IS_OWNED:
            founding_rule_text = (
                ""
                if self.city_founding_in_own_territory_rule
                else t_("ui.dialogs.unit.found_city.tile_already_owned.game_rule")
            )
            messenger.send(
                "ui.request.open.popup",
                [
                    "tile_already_owned",
                    t_("ui.dialogs.unit.found_city.tile_already_owned.title"),
                    t_(
                        "ui.dialogs.unit.found_city.tile_already_owned.message",
                        {"rule_text": str(founding_rule_text)},
                    ),
                ],
            )
        elif self.failure_reason == CantFoundReasons.TILE_IS_NOT_PASSABLE:
            messenger.send(
                "ui.request.open.popup",
                [
                    "tile_not_passable",
                    t_("ui.dialogs.unit.found_city.tile_not_passable.title"),
                    t_("ui.dialogs.unit.found_city.tile_not_passable.message"),
                ],
            )
        elif self.failure_reason == CantFoundReasons.OTHER_CITY_TO_CLOSE:
            distance_rule_text = (
                ""
                if self.city_founding_distance_rule == CITY_FOUNDING_DISTANCE_RADIUS_DEFAULT
                else t_(
                    "ui.dialogs.unit.found_city.city_too_close.game_rule",
                    {"distance": self.city_founding_distance_rule},
                )
            )
            messenger.send(
                "ui.request.open.popup",
                [
                    "city_too_close",
                    t_("ui.dialogs.unit.found_city.city_too_close.title"),
                    t_(
                        "ui.dialogs.unit.found_city.city_too_close.message",
                        {"distance_rule_text": distance_rule_text},
                    ),
                ],
            )
        return None

    def on_success(self, args: Tuple[Any], kwargs: Dict[Any, Any]) -> Optional[bool]:  # type: ignore
        from managers.player import PlayerManager

        messenger.send("unit.action.found_city.success", [self.tile])

        if self.tile is None:
            raise AssertionError("Tile was not found")

        if self.tile.city is None:
            raise AssertionError("City was not founded")

        if self.tile.owner == PlayerManager.player() and self.tile.city.player == PlayerManager.player():
            if self.tile.city.is_capital:
                title, message = (
                    t_("ui.dialogs.unit.found_city.founded_own_capital.title"),
                    t_("ui.dialogs.unit.found_city.founded_own_capital.message"),
                )
            else:
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

    def found_action_wrapper(self, *args: Any, **kwargs: Any) -> bool:
        self.tile = self.unit.tile  # This has to be done before the unit is destroyed otherwise the tile will be None.
        if self.unit.tile is None or not self.unit.tile.found(self.unit.owner):
            return False

        self.unit.destroy()
        return True

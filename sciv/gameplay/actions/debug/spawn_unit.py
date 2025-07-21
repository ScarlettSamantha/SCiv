from typing import TYPE_CHECKING, Any, Tuple, cast

from direct.showbase import MessengerGlobal
from gameplay.actions.debug.debug_action import DebugAction
from helpers.input import InputHelper
from managers.i18n import t_
from menus.kivy.parts.popup import DoubleSpinnerPopup

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.tile import Tile
    from gameplay.unit import Unit


class SpawnUnit(DebugAction):
    key = "actions.debug.spawn_unit"
    debug_action = True

    def __init__(self):
        super().__init__(
            name=self.key,
            action=self.run,
            condition=None,
            on_success=None,
            on_failure=None,
            success_condition=None,
        )
        self.on_the_spot_action = False
        self.targeting_tile_action = True
        self.tile: "Tile | None" = None

    def run(self, *args: Any, **kwargs: Any) -> None:
        from gameplay.repositories.unit import UnitRepository
        from managers.player import PlayerManager

        self.tile: "Tile | None" = cast("Tile | None", self.action_kwargs.get("target", None))

        if self.tile is None:
            raise ValueError("Tile must be set before spawning a unit.")

        if self.tile.units.has_any():
            MessengerGlobal.messenger.send(
                "ui.request.open.popup",
                [
                    "error",
                    t_("ui.dialogs.unit.move_errors.other_unit.title"),
                    t_("ui.dialogs.unit.move_errors.other_unit.message"),
                ],
            )
            return

        popup = DoubleSpinnerPopup(
            items1=[(str(unit.name), unit) for unit in UnitRepository.all().values()],
            items2=[
                (str(player.get_name()), player) for player in PlayerManager.all(add_mechanic_players=True).values()
            ],
            callback=self.spawn_unit,
            on_close=lambda: InputHelper.unlock_input(),
            title="Spawn Unit",
            ok_text="Spawn",
            cancel_text="Cancel",
        )
        InputHelper.lock_input()
        popup.open()

    def spawn_unit(self, unit_and_player: Tuple["Unit", "Player"]) -> None:
        unit, player = unit_and_player
        if self.tile is None:
            raise ValueError("Tile must be set before spawning a unit.")

        if not player.is_alive():
            raise ValueError("Cannot spawn a unit for a dead player.")

        if not unit:
            raise ValueError("Unit must be specified.")

        unit.spawn_on(self.tile, player, ignore_constraints=True)

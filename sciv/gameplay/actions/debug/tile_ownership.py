from typing import TYPE_CHECKING, Any, List, cast

from gameplay.actions.debug.debug_action import DebugAction
from helpers.input import InputHelper
from managers.game import World
from managers.player import PlayerManager
from menus.kivy.parts.popup import MenuPopup

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.player import Player
    from gameplay.tile import Tile


class TileOwnership(DebugAction):
    key = "actions.debug.tile_ownership"
    debug_action = True
    category = "Map"

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
        self.city: "City | None" = None
        self.tile: "Tile | None" = None

    def run(self, *args: Any, **kwargs: Any) -> None:
        from managers.player import PlayerManager

        self.tile: "Tile | None" = cast("Tile | None", self.action_kwargs.get("target", None))

        if self.tile is None:
            raise ValueError("Tile must be set before spawning a unit.")

        cities: List["City"] = []
        for player in PlayerManager.all().values():
            if player.is_alive():
                cities.extend(player.cities.all())  # type: ignore

        popup = MenuPopup(
            items=[(str(city.name), city) for city in cities],
            callback=self.change_ownership,
            on_close=lambda: InputHelper.unlock_input(),
            title="Spawn Unit",
            ok_text="Spawn",
            cancel_text="Cancel",
        )
        InputHelper.lock_input()
        popup.open()

    def change_ownership(self, city: "City") -> None:
        self.city = city
        player_manager: "PlayerManager | None" = PlayerManager.get_singleton_instance()
        assert player_manager is not None, "Player manager must be set before changing ownership."
        assert self.tile is not None, "Tile must be set before changing ownership."
        session_player: "Player" = player_manager.session_player()
        assert session_player is not None, "Session player must be set before changing ownership."
        world_manager: "World | None" = World.get_singleton_instance()
        assert world_manager is not None, "World manager must be set before changing ownership."
        world_manager.set_ownership_of_tile(self.tile, session_player, self.city)

from typing import TYPE_CHECKING, Any, Set, Type, cast

from gameplay.actions.debug.debug_action import DebugAction
from helpers.input import InputHelper
from menus.kivy.parts.popup import MenuPopup

from sciv.game import PathsHelper
from sciv.gameplay.terrain._base_terrain import BaseTerrain

if TYPE_CHECKING:
    from gameplay.terrain._base_terrain import BaseTerrain
    from gameplay.tile import Tile


class SetTerrainType(DebugAction):
    key = "actions.debug.set_terrain_type"
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
        from gameplay.repositories.terrain import TerrainRepository

        self.tile: "Tile | None" = cast("Tile | None", self.action_kwargs.get("target", None))

        if self.tile is None:
            raise ValueError("Tile must be set before trying to change the type.")

        terrain_types: Set[type[BaseTerrain]] = TerrainRepository.get_all()
        if len(terrain_types) == 0:  # I don't know why this happens but it does sometimes # TODO: investigate
            TerrainRepository.load(str(PathsHelper.get_terrain_dir()))
            terrain_types = TerrainRepository.get_all()
            if len(terrain_types) == 0:
                raise ValueError("No terrain types available to change to.")

        popup = MenuPopup(
            items=[(str(terrain.get_key()), terrain) for terrain in terrain_types],
            callback=self.change_terrain_type,
            on_close=lambda: InputHelper.unlock_input(),
            title="Change Terrain Type",
            ok_text="Change",
            cancel_text="Cancel",
        )
        popup.open()
        InputHelper.lock_input()

    def change_terrain_type(self, terrain_type: Type["BaseTerrain"]) -> None:
        from managers.game import Game

        if self.tile is None:
            raise ValueError("Tile must be set before changing terrain type.")

        self.tile.set_terrain(terrain=terrain_type())
        Game.get_singleton_instance().get_world_grid().update_tile(self.tile)

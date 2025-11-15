from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Type

from direct.showbase import MessengerGlobal
from gameplay.actions.debug.debug_action import DebugAction
from helpers.input import InputHelper
from managers.i18n import t_
from menus.kivy.parts.popup import DoubleSpinnerPopup

from gameplay.repositories.tile import TileRepository
from gameplay.repositories.resources import ResourceRepository
from gameplay.repositories.terrain import TerrainRepository


from gameplay.resource import BaseResource, ResourceType
from gameplay.terrain._base_terrain import BaseTerrain

if TYPE_CHECKING:
    from gameplay.tile import Tile


class SearchMap(DebugAction):
    key = "actions.debug.search_map"
    debug_action = True
    category = "Map"

    def __init__(self) -> None:
        super().__init__(
            name=self.key,
            action=self.run,
            condition=None,
            on_success=None,
            on_failure=None,
            success_condition=None,
        )
        self.on_the_spot_action = True
        self.targeting_tile_action = False

    def run(self, *args: Any, **kwargs: Any) -> None:
        terrains: List[Tuple[str, Optional[Type["BaseTerrain"]]]] = self._terrain_items()
        resources: List[Tuple[str, Optional[Type[BaseResource]]]] = self._resource_items()

        popup = DoubleSpinnerPopup(
            items1=terrains,
            items2=resources,
            callback=self._on_pick,
            on_close=None,
            title=t_("actions.debug.search_map.title"),
            ok_text=t_("ui.player_ui.generics.search"),
            cancel_text=t_("ui.player_ui.generics.cancel"),
        )
        InputHelper.lock_input()
        popup.open()

    def _terrain_items(self) -> List[Tuple[str, Optional[Type["BaseTerrain"]]]]:
        items: List[Tuple[str, Optional[Type["BaseTerrain"]]]] = [(str(t_("ui.player_ui.generics.any_terrain")), None)]
        terrs = sorted(list(TerrainRepository.get_all()), key=lambda cls: str(cls.get_name()))
        for terr_cls in terrs:
            key = str(terr_cls.get_name())
            items.append((key, terr_cls))
        return items

    def _resource_items(self) -> List[Tuple[str, Optional[Type[BaseResource]]]]:
        items: List[Tuple[str, Optional[Type[BaseResource]]]] = [(str(t_("ui.player_ui.generics.any_resource")), None)]
        res_classes = sorted(
            ResourceRepository.all_by_type([ResourceType.LUXURY, ResourceType.STRATEGIC, ResourceType.BONUS]),
            key=lambda cls: str(cls.name),
        )
        for res_cls in res_classes:
            label = str(res_cls.name)
            items.append((label, res_cls))
        return items

    def _on_pick(
        self,
        choice: Tuple[Optional[Type["BaseTerrain"]], Optional[Type[BaseResource]]],
    ) -> None:
        terrain_cls, resource_cls = choice
        matches = TileRepository.search(self._make_filter(terrain_cls, resource_cls))

        if not matches:
            MessengerGlobal.messenger.send(
                "ui.request.open.popup",
                [
                    "info",
                    t_("actions.debug.search_map.no_matches_title"),
                    t_("actions.debug.search_map.no_matches_message"),
                ],
            )
            return

        target: "Tile" = matches[0]
        self._jump_to_tile(target)

    def _make_filter(
        self,
        terrain_cls: Optional[Type["BaseTerrain"]],
        resource_cls: Optional[Type[BaseResource]],
    ) -> Callable[["Tile"], bool]:
        def terrain_matches(tile: "Tile") -> bool:
            if terrain_cls is None:
                return True
            terr: BaseTerrain = tile.get_terrain()
            return isinstance(terr, terrain_cls)

        def resource_matches(tile: "Tile") -> bool:
            if resource_cls is None:
                return True
            resources: Dict[str, BaseResource] = tile.resources.flatten_non_mechanic()
            for res in resources.values():
                if res.key == resource_cls.key:
                    return True
            return False

        return lambda tile: terrain_matches(tile) and resource_matches(tile)

    def _jump_to_tile(self, tile: "Tile") -> None:
        MessengerGlobal.messenger.send("game.camera.request.center_on_tile", [tile])

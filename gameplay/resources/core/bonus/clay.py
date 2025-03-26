from typing import Dict, Type

from gameplay.resources.core.bonus.bonus_resource import BaseBonusResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_grass import FlatGrass
from gameplay.tiles.base_tile import BaseTile
from managers.i18n import T_TranslationOrStr, _t
from system.generators.resource_allocator import ResourceAllocator


class Clay(BaseBonusResource):
    key: str = "resource.core.bonus.clay"
    name: T_TranslationOrStr = _t("content.resources.core.clay.name")
    description: T_TranslationOrStr = _t("content.resources.core.clay.description")
    icon: str = "assets/icons/resources/core/bonus/hex_border_clay.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        BaseTerrain: 0.0,
        FlatGrass: 100.0,
    }
    coverage = 0.4
    spawn_amount = 5.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)

    @classmethod
    def on_world_place_tile_filter(cls, resource_allocator: ResourceAllocator, tile: BaseTile) -> bool:
        if tile.is_coast is False:
            return False
        return True

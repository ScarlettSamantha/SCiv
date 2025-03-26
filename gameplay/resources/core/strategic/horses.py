from typing import Dict, Type

from gameplay.resources.core.strategic.strategic_resource import BaseStrategicResource
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.terrain.flat_grass import FlatGrass
from gameplay.terrain.flat_ice import FlatIce
from gameplay.terrain.flat_savanna import FlatSavanna
from gameplay.terrain.flat_scrubland import FlatScrubland
from gameplay.terrain.hills_grass import HillsGrass
from gameplay.tiles.hills_forrest import HillsForestTerrain
from managers.i18n import T_TranslationOrStr, _t


class Horses(BaseStrategicResource):
    key: str = "resource.core.strategic.horses"
    name: T_TranslationOrStr = _t("content.resources.core.horses.name")
    description: T_TranslationOrStr = _t("content.resources.core.horses.description")
    icon: str = "assets/icons/resources/core/strategic/bordered_horse.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = {
        FlatGrass: 50.0,
        FlatScrubland: 80.0,
        FlatSavanna: 50.0,
        FlatIce: 0.0,
        HillsGrass: 70.0,
        HillsForestTerrain: 40.0,
        BaseTerrain: 0.0,
    }
    spawn_amount = 5.0
    coverage = 2.0

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)

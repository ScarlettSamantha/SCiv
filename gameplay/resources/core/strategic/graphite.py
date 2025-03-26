from typing import Dict, Type

from gameplay.resources.core.strategic.strategic_resource import BaseStrategicResource
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import T_TranslationOrStr, _t


class Graphite(BaseStrategicResource):
    key: str = "resource.core.strategic.graphite"
    name: T_TranslationOrStr = _t("content.resources.core.graphite.name")
    description: T_TranslationOrStr = _t("content.resources.core.graphite.description")
    icon: str = "assets/icons/resources/core/strategic/bordered_thorium.png"
    spawn_chance: float | Dict[Type[BaseTerrain], float] = 100
    spawn_amount = 3.0
    coverage = 0.5

    def __init__(self, value: int | float = 0):
        super().__init__(value=value)

from typing import Any

from gameplay.improvements.core.resources.logging_camp import LoggingCamp
from gameplay.improvements.core.resources.mine import Mine
from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import t_


class HillsForest(BaseTerrain):
    _name = t_("world.terrain.hills_forest")
    movement_modifier = 0.5
    water_availability = 0.5
    _fallback_color = (91, 128, 64)
    _model = "assets/models/terrain/hill_forest.glb"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.add_supported_improvement(Mine)
        self.add_supported_improvement(LoggingCamp)
        self._texture = "hills_forest.png"

    def register_bits(self) -> None:
        # self.bits.add_bit(
        #     Bit(
        #         model="hill_grass_tree_rock.glb",
        #         scale=0.45,
        #         preferred_slot="center",
        #         allow_auto_scale=False,
        #         blocks_resource_model_spawning=True,
        #         offset=(0, 0, -0.3),
        #     )
        # )
        return super().register_bits()

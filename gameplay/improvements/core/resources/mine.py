from typing import Any

from gameplay.condition import Conditions, ResearchCondition
from gameplay.improvement import Improvement
from gameplay.techs.mining import Mining
from gameplay.yields import Yields
from managers.i18n import t_


class Mine(Improvement):
    name = t_("content.improvements.core.resources.mine.name")
    description = t_("content.improvements.core.resources.mine.description")
    placeable_on_tiles = True
    _model = "assets/models/tile_improvements/building_mine_blue.gltf"
    _model_scale = 0.33
    _model_hpr = (45, 0, 0)
    placeable_on_condition = Conditions(ResearchCondition(Mining, None))
    visible_condition = Conditions(ResearchCondition(Mining, None))
    tile_yield_improvement = Yields(production=1.0, mode=Yields.ADDITIVE)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50
        self._model_offset = (-0.20, 0.15, 0.09)

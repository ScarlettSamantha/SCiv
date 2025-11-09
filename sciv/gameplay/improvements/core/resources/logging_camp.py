from typing import Any

from gameplay.condition import Conditions, ResearchCondition
from gameplay.improvement import Improvement
from gameplay.techs.bronze_working import BronzeWorking
from gameplay.yields import Yields
from managers.i18n import t_


class LoggingCamp(Improvement):
    name = t_("content.improvements.core.resources.logging_camp.name")
    description = t_("content.improvements.core.resources.logging_camp.description")
    placeable_on_tiles = True
    _model = "assets/models/tile_improvements/building_lumbermill_blue.gltf"
    _model_scale = 0.33
    _model_hpr = (45, 0, 0)
    tile_yield_improvement = Yields(production=1.0, gold=1.0, mode=Yields.ADDITIVE)

    placeable_on_condition = Conditions(ResearchCondition(BronzeWorking, None))
    visible_condition = Conditions(ResearchCondition(BronzeWorking, None))

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

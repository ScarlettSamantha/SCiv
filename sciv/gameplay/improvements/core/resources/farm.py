from typing import Any

from gameplay.condition import Conditions, ResearchCondition
from gameplay.effects.improvement.farm import FarmEffect
from gameplay.improvement import Improvement
from gameplay.techs.pottery import Pottery
from gameplay.yields import Yields
from managers.i18n import t_


class Farm(Improvement):
    name = t_("content.improvements.core.resources.farm.name")
    description = t_("content.improvements.core.resources.farm.description")
    _model = "assets/models/tile_improvements/building_home_A_blue.gltf"
    _model_scale = 0.33
    _model_hpr = (45, 0, 0)
    placeable_on_tiles = True
    maintenance_cost = Yields(gold=1.0)

    placeable_on_condition = Conditions(ResearchCondition(Pottery, None))
    visible_condition = Conditions(ResearchCondition(Pottery, None))

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            *args,
            **kwargs,
        )

    def on_construct(self):
        self.effects.add_effect(FarmEffect(base_object=self, player=self.get_owner()))
        return super().on_construct()

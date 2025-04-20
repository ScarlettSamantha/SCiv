from typing import Any

from gameplay.improvement import Improvement, ImprovementBuildTurnMode


class BaseCityImprovement(Improvement):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.constructable_on_tile = False
        self.constructable_builder = False
        self.placeable_on_city = True
        self.placeable_by_player = True
        self.placeable_on_tiles = False
        self.multi_turn_mode = ImprovementBuildTurnMode.MULTI_TURN_RESOURCE

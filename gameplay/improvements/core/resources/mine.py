from gameplay.improvement import Improvement
from gameplay.yields import Yields
from managers.i18n import _t


class Mine(Improvement):
    name = _t("content.improvements.core.resources.mine.name")
    description = _t("content.improvements.core.resources.mine.description")
    placeable_on_tiles = True
    _model = "assets/models/tile_improvements/build_mine_blue.gltf"

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
        )

        self.health = 50
        self.max_health = 50

        self.tile_yield_improvement = Yields(production=1.0, mode=Yields.ADDITIVE)

from typing import Any

from gameplay.terrain.flat_scrubland import FlatScrubland as FlatScrublandTerrain
from gameplay.tiles.base_tile import BaseTile


class FlatScrubland(BaseTile):
    _terrain = FlatScrublandTerrain
    _model = _terrain.model

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.set_terrain(FlatScrublandTerrain())

from typing import Any

from gameplay.terrain._base_terrain import BaseTerrain
from managers.i18n import t_


class FlatWasteland(BaseTerrain):
    _name = t_("world.terrain.wasteland")
    movement_modifier = 0.5
    water_availability = 0.25
    radatiation = 1.0  # Keeping the attribute name as in the original code
    _model = "assets/models/tiles/wasteland.glb"
    _model = "assets/models/tiles/wasteland.glb"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

from gameplay.terrain.traits.land import mountain
from managers.i18n import T_TranslationOrStr

from ._base_terrain import BaseTerrain, rgb


class Mountain(BaseTerrain):
    _name = "world.terrain.mountain"
    _model = "assets/models/tiles/mountains3.glb"
    _texture: T_TranslationOrStr = "assets/models/tiles/mountain.png"
    _fallback_color = rgb(0, 119, 255)
    can_spawn_resources = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.movement_modifier = 3
        self.water_availability = 0

        self.passable: bool = False
        self.passable_without_tech: bool = False

        self.add_modifiers(mountain)

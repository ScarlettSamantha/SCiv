from typing import Any

from gameplay.bits import Bit, Bits
from gameplay.terrain._base_terrain import BaseTerrain
from gameplay.yields import Yields
from managers.i18n import T_TranslationOrStrOrNone, t_


class Lake(BaseTerrain):
    _name: T_TranslationOrStrOrNone = t_("world.terrain.lake")
    _model = "assets/models/terrain/lake.glb"
    _fallback_color = (0, 204, 255)
    model_pos_z_offset = -0.41

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.fallback_color = self._fallback_color
        self.movement_modifier = 0.5

        self._texture = "lake.png"
        self.tile_yield_base = Yields(food=1)

    def register_bits(self) -> None:
        lake_plants_a = Bit(model="water_plants_1.glb", scale=1.0, offset=(0, 0, 0))
        lake_plants_b = Bit(model="water_plants_2.glb", scale=1.0, offset=(0, 0, 0))
        lake_plants_c = Bit(model="water_plants_3.glb", scale=1.0, offset=(0, 0, 0))

        self.bits.empty_probability = 0.65

        self.bits.add_group("lake_plants").add_bit(lake_plants_a)
        self.bits.mode = self.bits.mode.OR

        self.bits.add_group("lake_plants_2").add_bit(lake_plants_a.copy())

        plant_3: Bits = self.bits.add_group("lake_plants_3")
        plant_3.add_bit(lake_plants_b)
        plant_3.add_bit(lake_plants_a.copy())

        plant_4: Bits = self.bits.add_group("lake_plants_4")
        plant_4.add_bit(lake_plants_c)
        plant_4.add_bit(lake_plants_a.copy())

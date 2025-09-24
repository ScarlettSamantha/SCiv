from typing import Any, Tuple

from gameplay.bits import Bit
from gameplay.terrain._base_terrain import BaseTerrain
from helpers.colors import Colors
from managers.i18n import t_


class SeaIce(BaseTerrain):
    _name = t_("world.terrain.sea_ice")
    movement_modifier = 1
    water_availability = 0.25
    _fallback_color: Tuple[float, float, float] = Colors.t4f_to_t3(Colors.WHITE)
    _model = "assets/models/terrain/sea.glb"
    model_pos_z_offset = -0.20
    _movement_modifier = 4.0

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._texture = "sea_ice.png"
        self.passable = False

    def register_bits(self) -> None:
        self.bits.mode = self.bits.mode.OR
        self.bits.empty_probability = 0.33

        water_ice_1 = Bit(model="water_ice_1.glb", scale=1.0, offset=(0, 0, 0))
        water_ice_2 = Bit(model="water_ice_2.glb", scale=1.0, offset=(0, 0, 0))
        water_ice_3 = Bit(model="water_ice_3.glb", scale=1.0, offset=(0, 0, 0))
        water_ice_4 = Bit(model="water_ice_4.glb", scale=1.0, offset=(0, 0, 0))
        water_ice_5 = Bit(model="water_ice_5.glb", scale=1.0, offset=(0, 0, 0))

        ice_a = self.bits.add_group("ice_a")
        ice_a.mode = self.bits.mode.AND
        ice_a.add_bit(water_ice_1.rotate(0).copy())
        ice_a.add_bit(water_ice_4.rotate(120).copy())
        ice_a.add_bit(water_ice_2.rotate(90).copy())
        ice_a.add_bit(water_ice_3.rotate(180).copy())

        ice_b = self.bits.add_group("ice_b")
        ice_b.mode = self.bits.mode.AND
        ice_b.add_bit(water_ice_2.rotate(150).copy())
        ice_b.add_bit(water_ice_3.rotate(140).copy())
        ice_b.add_bit(water_ice_4.rotate(30).copy())
        ice_b.add_bit(water_ice_5.rotate(210).copy())

        ice_c = self.bits.add_group("ice_c")
        ice_c.mode = self.bits.mode.AND
        ice_c.add_bit(water_ice_1.rotate(160).copy())
        ice_c.add_bit(water_ice_4.rotate(90).copy())
        ice_c.add_bit(water_ice_5.rotate(120).copy())

        ice_d = self.bits.add_group("ice_d")
        ice_d.mode = self.bits.mode.AND
        ice_d.add_bit(water_ice_3.rotate(90).copy())
        ice_d.add_bit(water_ice_1.rotate(270).copy())
        ice_d.add_bit(water_ice_4.rotate(180).copy())

        ice_e = self.bits.add_group("ice_e")
        ice_e.mode = self.bits.mode.AND
        ice_e.add_bit(water_ice_1.rotate(300).copy())
        ice_e.add_bit(water_ice_2.rotate(210).copy())
        ice_e.add_bit(water_ice_3.rotate(60).copy())
        ice_e.add_bit(water_ice_4.rotate(150).copy())

        ice_f = self.bits.add_group("ice_f")
        ice_f.mode = self.bits.mode.AND
        ice_f.add_bit(water_ice_4.rotate(0).copy())
        ice_f.add_bit(water_ice_4.rotate(240).copy())
        ice_f.add_bit(water_ice_5.rotate(330).copy())

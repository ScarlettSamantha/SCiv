import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from panda3d.core import NodePath

if TYPE_CHECKING:
    from gameplay.bits import Bit
    from gameplay.tile import Tile


class BitsRenderer:
    def __init__(self, tile: "Tile", parent: Optional[NodePath] = None) -> None:
        self.tile: "Tile" = tile
        self.prop_slots: Dict[str, Tuple[float, float, float]] = tile.get_prop_slots()
        self._bit_slot_assignments: Dict[str, "Bit"] = {}
        self._bit_models: Dict[str, NodePath] = {}
        self.parent: NodePath = parent if parent else tile.renderer.geometry_node

    def render(self) -> None:
        active_bits: Dict[str, "Bit"] = {b.id: b for b in self.tile.get_terrain().get_bits() if not b.is_disabled()}

        for slot, bit in list(self._bit_slot_assignments.items()):
            if bit.id not in active_bits:
                self._unrender_slot(slot)
                del self._bit_slot_assignments[slot]

        for bit in active_bits.values():
            if bit in self._bit_slot_assignments.values():
                continue
            slot = self._choose_slot_for(bit)
            if not slot:
                continue
            self._render_bit(bit, slot)

    def enable_bit(self, bit: "Bit", slot: Optional[str] = None) -> None:
        bit.disabled = False
        chosen = bit.get_preferred_slot_name() if bit.has_preferred_slot() else slot
        if not chosen:
            chosen = self._choose_slot_for(bit)
        if chosen:
            self._render_bit(bit, chosen)

    def disable_bit(self, bit: "Bit") -> None:
        bit.disabled = True
        if bit.id in self._bit_slot_assignments:
            slot_name = next((name for name, b in self._bit_slot_assignments.items() if b.id == bit.id), None)
            if slot_name:
                self._unrender_slot(slot_name)
                del self._bit_slot_assignments[slot_name]

    def search_bit(self, bit_id: str) -> Optional["Bit"]:
        return self.tile.get_terrain().bits.search_bit(bit_id)

    def _choose_slot_for(self, bit: "Bit") -> Optional[str]:
        if bit.has_preferred_slot():
            name = bit.get_preferred_slot_name()
            if name in self.prop_slots and self._slot_free(name):
                return name
            return None
        free = [s for s in self.prop_slots if self._slot_free(s)]
        return random.choice(free) if free else None

    def _slot_free(self, slot: str) -> bool:
        return slot not in self._bit_slot_assignments

    def _render_bit(self, bit: "Bit", slot_name: str) -> None:
        from system.tile_render import NET_TYPE

        self._bit_slot_assignments[slot_name] = bit
        model: NodePath | None = self.tile.renderer.add_model(
            model_path=bit.model,
            net_type=NET_TYPE.BIT,
            pos_offset=(
                bit.offset[0] + self.prop_slots[slot_name][0],
                bit.offset[1] + self.prop_slots[slot_name][1],
                bit.offset[2] + self.prop_slots[slot_name][2],
            ),
            scale=(bit.scale),
            hpr=bit.hpr,
            net_id=bit.id,
            disable_lighting=not bit.default_lighting,
            disable_shader=not bit.default_shader,
            parent=self.parent,
            flatten_model=False,
        )
        if model:
            self._bit_models[bit.id] = model

    def _unrender_slot(self, slot_name: str) -> None:
        bit: "Bit | None" = self._bit_slot_assignments.get(slot_name)
        if not bit:
            return

        self.tile.renderer.remove_model(bit.id)

    def disable_all(self) -> None:
        for bit in self.tile.get_terrain().get_bits():
            if not bit.is_disabled():
                self.disable_bit(bit)
        self._bit_slot_assignments.clear()

    def enable_all(self) -> None:
        for bit in self.tile.get_terrain().get_bits():
            if bit.is_disabled():
                self.enable_bit(bit)
        self._bit_slot_assignments.clear()

    def clear(self) -> None:
        for slot_name, _ in list(self._bit_slot_assignments.items()):
            self._unrender_slot(slot_name)
        self._bit_slot_assignments.clear()

    def on_inspect(self) -> Dict[str, str | None]:
        bits: List["Bit"] = self.tile.get_terrain().get_bits()
        loaded_bits: List[str] = [bit.id for bit in bits if not bit.is_disabled()]
        bits_str: str = ", ".join([f"{bit.id} ({bit.model})" for bit in bits])
        return {
            "terrain_bits": bits_str,
            "loaded_bits": ",".join(loaded_bits),
            "assigned_slots": str(self._bit_slot_assignments),
            "parent": self.parent.get_name() if self.parent else "None",
        }

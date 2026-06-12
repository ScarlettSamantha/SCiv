from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple
from zlib import crc32

from gameplay.bits import DisplayMode
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
        self._last_slot_by_bit_id: Dict[str, str] = {}

    def _unrender_all(self) -> None:
        for slot_name, _ in list(self._bit_slot_assignments.items()):
            self._unrender_slot(slot_name)
        self._bit_slot_assignments.clear()
        self._bit_models.clear()

    def _ordered_ids(self, ids: List[str]) -> List[str]:
        return sorted(ids, key=lambda s: (0 if s in self._last_slot_by_bit_id else 1, crc32(s.encode("utf-8"))))

    def render(self, include_details: bool = True) -> None:
        prev_assignments: Dict[str, "Bit"] = dict(self._bit_slot_assignments)
        for slot_name, bit in prev_assignments.items():
            self._last_slot_by_bit_id[bit.id] = slot_name

        self.prop_slots = self.tile.get_prop_slots()
        active_by_id: Dict[str, "Bit"] = self._gather_active_bits(include_details=include_details)

        new_assignments: Dict[str, "Bit"] = {}
        used_slots: Set[str] = set()

        self._unrender_all()

        for bit_id in self._ordered_ids(list(active_by_id.keys())):
            bit = active_by_id.get(bit_id)
            if not bit:
                continue

            pref: Optional[str] = bit.get_preferred_slot_name()
            if pref and pref in self.prop_slots and pref not in used_slots and self._slot_allowed(bit, pref):
                new_assignments[pref] = bit
                used_slots.add(pref)
                active_by_id.pop(bit_id, None)

        for old_slot, old_bit in prev_assignments.items():
            bit = active_by_id.get(old_bit.id)
            if (
                bit is not None
                and old_slot in self.prop_slots
                and old_slot not in used_slots
                and self._slot_allowed(bit, old_slot)
            ):
                new_assignments[old_slot] = bit
                used_slots.add(old_slot)
                active_by_id.pop(old_bit.id, None)

        for bit_id in self._ordered_ids(list(active_by_id.keys())):
            bit = active_by_id.get(bit_id)
            if not bit:
                continue

            last: Optional[str] = self._last_slot_by_bit_id.get(bit_id)
            if last and last in self.prop_slots and last not in used_slots and self._slot_allowed(bit, last):
                new_assignments[last] = bit
                used_slots.add(last)
                active_by_id.pop(bit_id, None)

        for bit_id in self._ordered_ids(list(active_by_id.keys())):
            bit = active_by_id.get(bit_id)
            if not bit:
                continue

            for slot_name in self._deterministic_slots_for(bit_id):
                if slot_name not in used_slots and self._slot_allowed(bit, slot_name):
                    new_assignments[slot_name] = bit
                    used_slots.add(slot_name)
                    active_by_id.pop(bit_id, None)
                    break

        for slot, bit in new_assignments.items():
            self._render_bit(bit, slot)
            self._last_slot_by_bit_id[bit.id] = slot

        self._bit_slot_assignments = new_assignments

    def enable_bit(self, bit: "Bit", slot: Optional[str] = None) -> None:
        bit.disabled = False

        if any(b.id == bit.id for b in self._bit_slot_assignments.values()):
            return

        chosen = self._choose_slot_for(bit, slot)
        if chosen is None:
            return

        self._render_bit(bit, chosen)
        self._bit_slot_assignments[chosen] = bit
        self._last_slot_by_bit_id[bit.id] = chosen

    def disable_bit(self, bit: "Bit") -> None:
        bit.disabled = True
        slot_name: Optional[str] = next(
            (name for name, b in self._bit_slot_assignments.items() if b.id == bit.id), None
        )
        if slot_name:
            self._unrender_slot(slot_name)
            self._bit_slot_assignments.pop(slot_name, None)

    def search_bit(self, bit_id: str) -> Optional["Bit"]:
        return self.tile.get_terrain().bits.search_bit(bit_id)

    def add_bit(self, bit: "Bit", slot: Optional[str] = None) -> None:
        if any(b.id == bit.id for b in self._bit_slot_assignments.values()):
            return

        chosen = self._choose_slot_for(bit, slot)
        if chosen is None:
            return

        self._render_bit(bit, chosen)
        self._bit_slot_assignments[chosen] = bit
        self._last_slot_by_bit_id[bit.id] = chosen

    def remove_bit(self, bit: "Bit") -> None:
        slot_name: Optional[str] = next(
            (name for name, b in self._bit_slot_assignments.items() if b.id == bit.id), None
        )
        if slot_name:
            self._unrender_slot(slot_name)
            self._bit_slot_assignments.pop(slot_name, None)

    def disable_all(self) -> None:
        for slot_name, _ in list(self._bit_slot_assignments.items()):
            self._unrender_slot(slot_name)
        self._bit_slot_assignments.clear()

    def enable_all(self) -> None:
        for bit in self.tile.get_terrain().get_bits():
            if bit.is_disabled():
                self.enable_bit(bit)

    def clear(self) -> None:
        for slot_name, _ in list(self._bit_slot_assignments.items()):
            self._unrender_slot(slot_name)
        self._bit_slot_assignments.clear()
        self._bit_models.clear()
        self.prop_slots = self.tile.get_prop_slots()

    def on_inspect(self) -> Dict[str, Optional[str]]:
        bits: List["Bit"] = self.tile.get_terrain().get_bits()
        loaded_bits: List[str] = [bit.id for bit in bits if not bit.is_disabled()]
        bits_str: str = ", ".join([f"{bit.id} ({bit.model})" for bit in bits])
        return {
            "terrain_bits": bits_str,
            "loaded_bits": ",".join(loaded_bits),
            "assigned_slots": str(self._bit_slot_assignments),
            "remembered_slots": str(self._last_slot_by_bit_id),
            "parent": self.parent.get_name() if self.parent else "None",
        }

    def has_any_resource_override_bits(self) -> bool:
        for bit in self._bit_slot_assignments.values():
            if bit.blocks_resource_model():
                return True
        return False

    def _gather_active_bits(self, include_details: bool = True) -> Dict[str, "Bit"]:
        active_bits: Dict[str, "Bit"] = {}
        resource_bits: List["Bit"] = []
        terrain_bits: List["Bit"] = []
        improvement_bits: List["Bit"] = []
        city_bits: List["Bit"] = []

        if self.tile.is_city() and self.tile.city:
            if include_details:
                for improvement in self.tile.city.get_improvements():
                    improvement_bit: Optional["Bit"] = improvement.as_bit()
                    if improvement_bit:
                        city_bits.append(improvement_bit)
            else:
                terrain_bits = self.tile.get_terrain().get_bits()
        else:
            terrain_bits = self.tile.get_terrain().get_bits()

            if include_details:
                for resource in self.tile.get_resources():
                    resource_bit: Optional["Bit"] = resource.as_bit(self.tile.is_land)
                    if resource_bit:
                        resource_bits.append(resource_bit)

                for improvement in self.tile.get_improvements().get_all():
                    improvement_bit: Optional["Bit"] = improvement.as_bit()
                    if improvement_bit:
                        improvement_bits.append(improvement_bit)

        has_units: bool = self.tile.units.has_any()
        has_resources: bool = self.tile.resources.has_non_mechanical_resources()
        has_improvements: bool = self.tile.get_improvements().has_any()
        is_selected: bool = self.tile.is_selected

        for bit in terrain_bits + resource_bits + city_bits + improvement_bits:
            if bit.is_disabled():
                continue

            modes: List[DisplayMode] = bit.get_display_mode()

            if DisplayMode.HIDE_ON_UNIT in modes and has_units:
                continue
            if DisplayMode.HIDE_ON_RESOURCE in modes and has_resources:
                continue
            if DisplayMode.HIDE_ON_SELECT in modes and is_selected:
                continue
            if DisplayMode.HIDE_ON_RESOURCE_IMPROVEMENT in modes and has_improvements:
                continue

            active_bits[bit.id] = bit

        return active_bits

    def _slot_allowed(self, bit: "Bit", slot: str) -> bool:
        clear_center_flag = bool(getattr(bit, "display_mode", 0) & DisplayMode.CLEAR_CENTER_SLOT.value)
        if clear_center_flag:
            return slot == "center"
        if bit.has_preferred_slot():
            return slot == bit.get_preferred_slot_name()
        return True

    def _slot_valid_and_free(self, bit: "Bit", slot: str) -> bool:
        return slot in self.prop_slots and self._slot_free(slot) and self._slot_allowed(bit, slot)

    def _deterministic_slots_for(self, bit_id: str) -> List[str]:
        slots = sorted(self.prop_slots.keys())
        if not slots:
            return []
        offset = crc32(bit_id.encode("utf-8")) % len(slots)
        return slots[offset:] + slots[:offset]

    def _choose_slot_for(self, bit: "Bit", requested_slot: Optional[str] = None) -> Optional[str]:
        self.prop_slots = self.tile.get_prop_slots()

        if bit.has_preferred_slot():
            name = bit.get_preferred_slot_name()
            if name is not None and self._slot_valid_and_free(bit, name):
                return name
            return None

        if requested_slot is not None:
            if self._slot_valid_and_free(bit, requested_slot):
                return requested_slot
            return None

        last = self._last_slot_by_bit_id.get(bit.id)
        if last and self._slot_valid_and_free(bit, last):
            return last

        for slot_name in self._deterministic_slots_for(bit.id):
            if self._slot_valid_and_free(bit, slot_name):
                return slot_name

        return None

    def _slot_free(self, slot: str) -> bool:
        return slot not in self._bit_slot_assignments

    def _render_bit(self, bit: "Bit", slot_name: str) -> None:
        from system.renderers.tile_renderer import NET_TYPE

        self.prop_slots = self.tile.get_prop_slots()
        if slot_name not in self.prop_slots:
            return

        if bit.id in self._bit_models:
            self.tile.renderer.remove_model(self._net_id(bit.id))
            self._bit_models.pop(bit.id, None)

        pos = self.prop_slots[slot_name]

        model: Optional[NodePath] = self.tile.renderer.add_model(
            model_path=bit.model,
            net_type=NET_TYPE.BIT,
            pos_offset=(bit.offset[0] + pos[0], bit.offset[1] + pos[1], bit.offset[2] + pos[2]),
            scale=bit.scale,
            hpr=bit.hpr,
            net_id=self._net_id(bit.id),
            disable_lighting=not bit.default_lighting,
            disable_shader=not bit.default_shader,
            parent=self.parent,
            flatten_model=False,
        )
        if model:
            self._bit_models[bit.id] = model

    def _net_id(self, bit_id: str) -> str:
        return f"{self.tile.x}_{self.tile.y}_{bit_id}"

    def _unrender_slot(self, slot_name: str) -> None:
        bit: Optional["Bit"] = self._bit_slot_assignments.get(slot_name)
        if not bit:
            return
        self.tile.renderer.remove_model(self._net_id(bit.id))
        self._bit_models.pop(bit.id, None)

    def dump(self) -> Dict[str, Any]:
        return {
            "last_slot_by_bit_id": self._last_slot_by_bit_id,
            "prop_slots": self.prop_slots,
            "bit_slot_assignments": {k: v.id for k, v in self._bit_slot_assignments.items()},
        }

    def load(self, data: Dict[str, Any]) -> None:
        self._last_slot_by_bit_id = data.get("last_slot_by_bit_id", {})
        self.prop_slots = data.get("prop_slots", self.tile.get_prop_slots())
        bit_assignments: Dict[str, str] = data.get("bit_slot_assignments", {})
        self._bit_slot_assignments.clear()

        for slot, bit_id in bit_assignments.items():
            bit = self.search_bit(bit_id)
            if bit and slot in self.prop_slots and self._slot_allowed(bit, slot):
                self._bit_slot_assignments[slot] = bit
                self._last_slot_by_bit_id[bit.id] = slot
import random
import uuid
from copy import copy
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from managers.input import NET_TYPE
from panda3d.core import NodePath, PandaNode

if TYPE_CHECKING:
    from gameplay.tile import Tile


class GroupMode(Enum):
    OR = "or"
    AND = "and"

    def __getstate__(self) -> object:
        return {"name": self.name, "value": self.value}


class Bit:
    BASE_PATH = "assets/models/bits/"

    def __init__(
        self,
        model: str,
        scale: float = 1.0,
        offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        preferred_slot: Optional[str] = None,
        allow_auto_scale: bool = True,
        disabled: bool = False,
        blocks_resource_model_spawning: bool = False,
        id: Optional[str] = None,
        default_shader: bool = True,
        default_lighting: bool = True,
    ):
        self.id: str = id or uuid.uuid4().hex
        self.model: str = model if model.__contains__(self.BASE_PATH) else f"{self.BASE_PATH}{model}"
        self.scale: float = scale
        self.offset: Tuple[float, float, float] = offset
        self.hpr: Tuple[float, float, float] = hpr
        self.preferred_slot: Optional[str] = preferred_slot
        self.net_tag: str = uuid.uuid4().hex
        self.allow_auto_scale: bool = allow_auto_scale
        self.disabled: bool = disabled
        self.blocks_resource_model_spawning: bool = blocks_resource_model_spawning
        self.default_shader: bool = default_shader
        self.default_lighting: bool = default_lighting

    def copy(
        self,
        scale: Optional[float] = None,
        offset: Optional[Tuple[float, float, float]] = None,
        hpr: Optional[Tuple[float, float, float]] = None,
    ) -> "Bit":
        _copy = copy(self)
        _copy.id = str(uuid.uuid4().hex)
        _copy.scale = scale if scale is not None else self.scale
        _copy.offset = offset if offset is not None else self.offset
        _copy.hpr = hpr if hpr is not None else self.hpr
        return _copy

    def rotate(self, h: float = 0.0, p: float = 0.0, r: float = 0.0) -> "Bit":
        self.hpr = (h, p, r)
        return self

    def scaleBit(self, factor: float) -> "Bit":
        self.scale *= factor
        return self

    def __getstate__(self) -> object:
        state = self.__dict__.copy()
        return state

    def is_disabled(self) -> bool:
        return self.disabled

    def has_preferred_slot(self) -> bool:
        return self.preferred_slot is not None

    def get_preferred_slot_name(self) -> Optional[str]:
        return self.preferred_slot


class Bits:
    def __init__(
        self,
        mode: GroupMode = GroupMode.OR,
        name: Optional[str] = None,
        parent: Optional["Bits"] = None,
    ) -> None:
        self.mode: GroupMode = mode
        self.name: Optional[str] = name
        self.parent: Optional["Bits"] = parent
        self.bits: Dict[str, Bit] = {}
        self.groups: Dict[str, "Bits"] = {}
        self.enabled: bool = True
        self.disabled_bits: Dict[str, Bit] = {}
        self.empty_probability: float = 0.0

    @property
    def full_path(self) -> str:
        if self.parent and self.name:
            parent_path = self.parent.full_path
            return f"{parent_path}.{self.name}" if parent_path else self.name
        return ""

    def __getstate__(self) -> object:
        state = self.__dict__.copy()
        state.pop("parent", None)
        state["mode"] = self.mode.name
        if self.bits:
            state["bits"] = {
                k: f"{v.__module__}.{v.__class__.__name__}.{str(v.model.replace('/', '_'))}"
                for k, v in self.bits.items()
            }
        else:
            state["bits"] = {}
        return state

    def _get_full_bit_key(self, bit_id: str) -> str:
        path = self.full_path
        return f"{path}.{bit_id}" if path else bit_id

    def add_group(self, name: str, mode: Optional[GroupMode] = None) -> "Bits":
        if name in self.bits:
            raise ValueError(f"Group name '{name}' conflicts with an existing bit ID")
        if name in self.groups:
            return self.groups[name]
        grp_mode = mode if mode is not None else self.mode
        sub = Bits(mode=grp_mode, name=name, parent=self)
        self.groups[name] = sub
        return sub

    def add_bit(self, bit: Bit, group: Optional[str] = None) -> "Bits":
        if group:
            if group not in self.groups:
                self.add_group(group)
            self.groups[group].add_bit(bit)
        else:
            if bit.id in self.groups:
                raise ValueError(f"Bit ID '{bit.id}' conflicts with existing group name")
            if bit.id in self.bits:
                raise ValueError(f"Bit ID '{bit.id}' already exists in this group")
            self.bits[bit.id] = bit
            if bit.disabled:
                self.disabled_bits[bit.id] = bit
        return self

    def remove_bit(self, bit: Bit) -> None:
        if bit.id in self.bits:
            self.disabled_bits.pop(bit.id, None)
            del self.bits[bit.id]
        for sub in self.groups.values():
            sub.remove_bit(bit)

    def _set_disabled_state(self, parts: List[str], disabled: bool) -> None:
        if not parts:
            return
        key = parts[0]
        if key in self.groups:
            self.groups[key]._set_disabled_state(parts[1:], disabled)
        else:
            if not (bit := self.bits.get(key)):
                return
            bit.disabled = disabled
            if disabled:
                self.disabled_bits[key] = bit
            else:
                self.disabled_bits.pop(key, None)

    def disable_bit(self, full_key: str) -> None:
        parts = full_key.split(".")
        self._set_disabled_state(parts, True)

    def enable_bit(self, full_key: str) -> None:
        parts = full_key.split(".")
        self._set_disabled_state(parts, False)

    def search_bit(self, full_key: str) -> Optional[Bit]:
        parts = full_key.split(".")
        return self._search_bit_parts(parts)

    def _search_bit_parts(self, parts: List[str]) -> Optional[Bit]:
        if not parts:
            return None
        key = parts[0]
        if key in self.groups:
            return self.groups[key]._search_bit_parts(parts[1:])
        return self.bits.get(key)

    def get_groups(self, groups: List[str] = []) -> Dict[str, "Bits"]:
        if not groups:
            return self.groups
        return {name: self.groups[name] for name in groups if name in self.groups}

    def choose(self, num: int = 1, group: Optional[str] = None, allow_empty_probability: bool = True) -> List[Bit]:
        if allow_empty_probability and self.empty_probability > 0.0:
            if random.uniform(0.0, 1.0) < self.empty_probability:
                return []

        container = self if group is None else self.groups.get(group)
        if container is None or not container.enabled:
            return []

        return container._collect_recursive()

    def is_disabled(self) -> bool:
        if not self.enabled:
            return True
        for bit in self.bits.values():
            if not bit.disabled:
                return False
        for sub in self.groups.values():
            if not sub.is_disabled():
                return False
        return True

    def _collect_recursive(self) -> List[Bit]:
        if not self.enabled:
            return []
        result: List[Bit] = []
        if self.mode == GroupMode.AND:
            result.extend(self.bits.values())
            for sub in self.groups.values():
                result.extend(sub._collect_recursive())
        else:  # OR mode
            if self.bits:
                result.append(random.choice(list(self.bits.values())))
            if self.groups:
                sub = random.choice(list(self.groups.values()))
                result.extend(sub._collect_recursive())
        return result

    def clear(self) -> None:
        self.bits.clear()
        self.groups.clear()
        self.disabled_bits.clear()


class BitsRenderer:
    def __init__(self, tile: "Tile", parent: Optional[NodePath] = None) -> None:
        self.tile: "Tile" = tile
        self.prop_slots: Dict[str, Tuple[float, float, float]] = tile.get_prop_slots()
        self._bit_slot_assignments: Dict[str, Bit] = {}
        self.parent: NodePath[PandaNode] = parent if parent else tile.renderer.geometry_node

    def render(self) -> None:
        active_bits = {b.id: b for b in self.tile.get_terrain().get_bits() if not b.is_disabled()}

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

    def enable_bit(self, bit: Bit, slot: Optional[str] = None) -> None:
        bit.disabled = False
        chosen = bit.get_preferred_slot_name() if bit.has_preferred_slot() else slot
        if not chosen:
            chosen = self._choose_slot_for(bit)
        if chosen:
            self._render_bit(bit, chosen)

    def disable_bit(self, bit: Bit) -> None:
        bit.disabled = True
        if bit.id in self._bit_slot_assignments:
            slot_name = next((name for name, b in self._bit_slot_assignments.items() if b.id == bit.id), None)
            if slot_name:
                self._unrender_slot(slot_name)
                del self._bit_slot_assignments[slot_name]

    def search_bit(self, bit_id: str) -> Optional[Bit]:
        return self.tile.get_terrain().bits.search_bit(bit_id)

    def _choose_slot_for(self, bit: Bit) -> Optional[str]:
        if bit.has_preferred_slot():
            name = bit.get_preferred_slot_name()
            if name in self.prop_slots and self._slot_free(name):
                return name
            return None
        free = [s for s in self.prop_slots if self._slot_free(s)]
        return random.choice(free) if free else None

    def _slot_free(self, slot: str) -> bool:
        return slot not in self._bit_slot_assignments

    def _render_bit(self, bit: Bit, slot_name: str) -> None:
        self._bit_slot_assignments[slot_name] = bit
        model: NodePath[PandaNode] | None = self.tile.renderer.add_model(
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
        if model is not None:
            model.flatten_strong()

    def _unrender_slot(self, slot_name: str) -> None:
        bit = self._bit_slot_assignments.get(slot_name)
        if not bit:
            return

        self.tile.renderer.remove_model(bit.model)

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
        bits: List[Bit] = self.tile.get_terrain().get_bits()
        loaded_bits: List[str] = [bit.id for bit in bits if not bit.is_disabled()]
        bits_str: str = ", ".join([f"{bit.id} ({bit.model})" for bit in bits])
        return {
            "terrain_bits": bits_str,
            "loaded_bits": ",".join(loaded_bits),
            "assigned_slots": str(self._bit_slot_assignments),
            "parent": self.parent.get_name() if self.parent else "None",
        }

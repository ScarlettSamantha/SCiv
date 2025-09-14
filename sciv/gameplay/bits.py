import random
import uuid
from copy import copy
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class DisplayMode(Enum):
    SHOW_ALWAYS = 0b00000000
    HIDE_ON_UNIT = 0b00000001
    HIDE_ON_RESOURCE = 0b00000010
    HIDE_ON_SELECT = 0b00000100
    CLEAR_CENTER_SLOT = 0b00001000
    OVERRULES_RESOURCE_MODEL = 0b00010000


class GroupMode(Enum):
    OR = "or"
    AND = "and"

    def dump(self) -> Dict[str, Any]:
        return {"name": self.name, "value": self.value}

    def load(self, data: Dict[str, Any]) -> "GroupMode":
        name = data.get("name", self.name)
        return GroupMode[name]


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
        display_mode: int = DisplayMode.SHOW_ALWAYS.value,
    ):
        self.id: str = id or uuid.uuid4().hex
        self.model: str = model if model.__contains__(self.BASE_PATH) else f"{self.BASE_PATH}{model}"
        self.scale: float = scale
        self.offset: Tuple[float, float, float] = offset
        self.hpr: Tuple[float, float, float] = hpr
        self.preferred_slot: Optional[str] = preferred_slot
        self.net_tag: str = id or uuid.uuid4().hex
        self.allow_auto_scale: bool = allow_auto_scale
        self.disabled: bool = disabled
        self.blocks_resource_model_spawning: bool = blocks_resource_model_spawning
        self.default_shader: bool = default_shader
        self.default_lighting: bool = default_lighting
        self.display_mode: int = display_mode

    def copy(
        self,
        scale: Optional[float] = None,
        offset: Optional[Tuple[float, float, float]] = None,
        hpr: Optional[Tuple[float, float, float]] = None,
    ) -> "Bit":
        _copy = copy(self)
        _copy.id = str(uuid.uuid4().hex)
        _copy.net_tag = _copy.id or uuid.uuid4().hex
        _copy.scale = scale if scale is not None else self.scale
        _copy.offset = offset if offset is not None else self.offset
        _copy.hpr = hpr if hpr is not None else self.hpr
        _copy.display_mode = self.display_mode
        return _copy

    def dump(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "scale": self.scale,
            "offset": self.offset,
            "hpr": self.hpr,
            "preferred_slot": self.preferred_slot,
            "allow_auto_scale": self.allow_auto_scale,
            "disabled": self.disabled,
            "blocks_resource_model_spawning": self.blocks_resource_model_spawning,
            "net_tag": self.net_tag,
            "display_mode": self.display_mode,
            "cls_ref": f"{self.__module__}.{self.__class__.__name__}",
        }

    def load_dump(self, data: Dict[str, Any]) -> "Bit":
        self.id = data.get("id", self.id)
        self.scale = data.get("scale", self.scale)
        self.offset = tuple(data.get("offset", self.offset))
        self.hpr = tuple(data.get("hpr", self.hpr))
        self.preferred_slot = data.get("preferred_slot", self.preferred_slot)
        self.allow_auto_scale = data.get("allow_auto_scale", self.allow_auto_scale)
        self.disabled = data.get("disabled", self.disabled)
        self.display_mode = data.get("display_mode", self.display_mode)
        self.blocks_resource_model_spawning = data.get(
            "blocks_resource_model_spawning",
            self.blocks_resource_model_spawning,
        )
        self.net_tag = data.get("net_tag", self.net_tag)
        return self

    def get_display_mode(self) -> List[DisplayMode]:
        modes: List[DisplayMode] = []
        for mode in DisplayMode:
            if self.display_mode & mode.value:
                modes.append(mode)
        return modes

    def show_on_unit(self) -> bool:
        return not (self.display_mode & DisplayMode.HIDE_ON_UNIT.value)

    def show_on_resource(self) -> bool:
        return not (self.display_mode & DisplayMode.HIDE_ON_RESOURCE.value)

    def show_on_select(self) -> bool:
        return not (self.display_mode & DisplayMode.HIDE_ON_SELECT.value)

    def blocks_resource_model(self) -> bool:
        return bool(self.display_mode & DisplayMode.OVERRULES_RESOURCE_MODEL.value)

    def rotate(self, h: float = 0.0, p: float = 0.0, r: float = 0.0) -> "Bit":
        self.hpr = (h, p, r)
        return self

    def scaleBit(self, factor: float) -> "Bit":
        self.scale *= factor
        return self

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

    def dump(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        if self.bits:
            result["bits"] = {k: v.dump() for k, v in self.bits.items()}
        if self.groups:
            result["groups"] = {k: v.dump() for k, v in self.groups.items()}
        result["mode"] = self.mode.value
        result["enabled"] = self.enabled
        result["empty_probability"] = self.empty_probability
        return result

    def load(self, data: Dict[str, Any]) -> "Bits":
        self.mode = GroupMode[data.get("mode", self.mode.name)]
        self.enabled = data.get("enabled", self.enabled)
        self.empty_probability = data.get("empty_probability", self.empty_probability)
        bits_data = data.get("bits", {})
        for k, v in bits_data.items():
            bit = Bit(model="")
            bit.load_dump(v)
            self.bits[k] = bit
            if bit.disabled:
                self.disabled_bits[k] = bit
        groups_data = data.get("groups", {})
        for k, v in groups_data.items():
            group = Bits(parent=self, name=k)
            group.load(v)
            self.groups[k] = group
        return self

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

    def has_bit_active_with_resource_blocking(self) -> bool:
        for bit in self.bits.values():
            if not bit.disabled and bit.blocks_resource_model():
                return True
        for sub in self.groups.values():
            if sub.has_bit_active_with_resource_blocking():
                return True
        return False

    def clear(self) -> None:
        self.bits.clear()
        self.groups.clear()
        self.disabled_bits.clear()

from __future__ import annotations
import random
from enum import Enum
from typing import Dict, List, Optional, Tuple


class GroupMode(Enum):
    """
    Determines how bits and subgroups are combined:
    - OR: randomly select one bit or one subgroup per level
    - AND: include all bits and recurse into all subgroups
    """

    OR = "or"
    AND = "and"


class Bit:
    """
    Represents a single game prop or bit, with model path and transform.
    """

    BASE_PATH = "assets/models/bits/"

    def __init__(
        self,
        model: str,
        scale: float = 1.0,
        offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        # Ensure full path
        self.model = model if model.startswith(self.BASE_PATH) else f"{self.BASE_PATH}{model}"
        self.scale = scale
        self.offset = offset
        self.hpr = hpr

    def copy(
        self,
        scale: Optional[float] = None,
        offset: Optional[Tuple[float, float, float]] = None,
        hpr: Optional[Tuple[float, float, float]] = None,
    ) -> Bit:
        return Bit(
            model=self.model,
            scale=scale if scale is not None else self.scale,
            offset=offset if offset is not None else self.offset,
            hpr=hpr if hpr is not None else self.hpr,
        )


class Bits:
    def __init__(self, mode: GroupMode = GroupMode.OR) -> None:
        self.mode: GroupMode = mode
        self.bits: List[Bit] = []
        self.groups: Dict[str, Bits] = {}
        self.enabled: bool = True

    def add_bit(self, bit: Bit, group: Optional[str] = None) -> Bits:
        if group:
            sub = self.groups.setdefault(group, Bits(mode=self.mode))
            sub.add_bit(bit)
        else:
            self.bits.append(bit)
        return self

    def add_group(self, name: str, mode: Optional[GroupMode] = None) -> Bits:
        grp_mode = mode if mode is not None else self.mode
        sub = Bits(mode=grp_mode)
        self.groups[name] = sub
        return sub

    def remove_bit(self, bit: Bit) -> None:
        if bit in self.bits:
            self.bits.remove(bit)
        for sub in self.groups.values():
            sub.remove_bit(bit)

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def is_enabled(self) -> bool:
        return self.enabled

    def choose(self, num: int = 1, group: Optional[str] = None) -> List[Bit]:
        container = self if group is None else self.groups.get(group)
        if container is None or not container.enabled:
            return []
        collected = container._collect_recursive()
        if container.mode == GroupMode.OR:
            return random.sample(collected, min(num, len(collected)))
        return collected

    def _collect_recursive(self) -> List[Bit]:
        if not self.enabled:
            return []
        result: List[Bit] = []
        if self.mode == GroupMode.AND:
            result.extend(self.bits)
            for sub in self.groups.values():
                result.extend(sub._collect_recursive())
        else:
            if self.bits:
                result.append(random.choice(self.bits))
            if self.groups:
                sub = random.choice(list(self.groups.values()))
                result.extend(sub._collect_recursive())
        return result

    def clear(self) -> None:
        self.bits.clear()
        self.groups.clear()

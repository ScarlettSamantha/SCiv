from dataclasses import dataclass
from typing import Any

HexCoord = tuple[int, int]


@dataclass(frozen=True, slots=True)
class DynamicOptionProfile:
    key: str
    name: str
    description: str
    params: dict[str, Any]


@dataclass(frozen=True, slots=True)
class NamedLandmass:
    id: str
    name: str
    kind: str
    size: int
    tiles: tuple[HexCoord, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "size": self.size,
            "anchor": self.tiles[0] if self.tiles else None,
        }


@dataclass(frozen=True, slots=True)
class NamedBiomeRegion:
    id: str
    name: str
    biome_key: str
    biome_title: str
    size: int
    tiles: tuple[HexCoord, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "biome": self.biome_key,
            "biome_title": self.biome_title,
            "size": self.size,
            "anchor": self.tiles[0] if self.tiles else None,
        }


@dataclass(frozen=True, slots=True)
class NamedRiver:
    id: str
    name: str
    length: int
    source: HexCoord
    mouth: HexCoord | None
    tiles: tuple[HexCoord, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "length": self.length,
            "source": self.source,
            "mouth": self.mouth,
        }

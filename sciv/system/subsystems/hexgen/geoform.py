from typing import TYPE_CHECKING, List, Set
import uuid


from system.subsystems.hexgen.hex import Hex

if TYPE_CHECKING:
    from system.subsystems.hexgen.enums import GeoformType


class Geoform:
    """A landmass or water feature"""

    def __init__(self, hexes: set["Hex"], geotype: "GeoformType"):
        self.type = geotype  # GeoformType
        self.hexes: Set["Hex"] = hexes  # set
        self.size = len(hexes)
        self.id = uuid.uuid4()  # uuid
        self.neighbors: set["Geoform"] = set()  # set of Geoform
        self.to_delete = False

        for h in hexes:
            h.geoform = self

    def to_dict(self) -> dict[str, str | int]:
        """Dictionary representation"""
        return {"id": self.id.hex, "type": self.type.name, "size": self.size}

    def neighbor_of_type(self, other_type: "GeoformType") -> list["Geoform"]:
        """
        Returns all neighbors of a given type
        """
        result: List["Geoform"] = []
        for n in self.neighbors:
            if n.type is other_type:
                result.append(n)
        return result

    def neighbor_of_types(self, other_types: List["GeoformType"]) -> list["Geoform"]:
        result: list["Geoform"] = []
        for t in other_types:
            result.extend(self.neighbor_of_type(t))
        return result

    def merge(self, other: "Geoform") -> None:
        """Merge another Geoform into this one"""
        # add their hexes to mine
        self.hexes.update(other.hexes)
        self.size += len(other.hexes)
        # set their hexes to me
        for h in other.hexes:
            h.geoform = self
        # empty their hexes
        other.hexes = set()
        other.size = 0
        # mark them to be deleted
        other.to_delete = True

    def is_geotype(self, geotype: "GeoformType") -> bool:
        """Is this geoform this type?"""
        return self.type is geotype

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Geoform):
            return NotImplemented
        return self.id == other.id

    def __key(self) -> uuid.UUID:
        return self.id

    def __hash__(self) -> int:
        return hash(self.__key())

    def __str__(self) -> str:
        return "<Geoform: type: {}, size: {}, id: {}>".format(self.type.get(1), self.size, self.id)

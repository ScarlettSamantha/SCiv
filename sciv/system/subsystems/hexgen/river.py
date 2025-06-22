from typing import TYPE_CHECKING
import uuid

from system.subsystems.hexgen.edge import Edge
from system.subsystems.hexgen.enums import HexSide

if TYPE_CHECKING:
    from system.generators.basic import Grid


class RiverSegment:
    def __init__(self, grid: "Grid", x: int, y: int, side: HexSide, is_source: bool = False):
        self.grid: "Grid" = grid
        self.x: int = x
        self.y: int = y
        self.side: HexSide = side
        self.is_source: bool = is_source
        self.next: "RiverSegment | None" = None

        self.id: uuid.UUID = uuid.uuid4()

    @property
    def hex(self):
        return self.grid.find_hex(self.x, self.y)

    @property
    def edge(self) -> Edge:
        r = self.hex.get_edge(self.side)
        if r is None:
            raise ValueError("No edge found")
        return r

    def __repr__(self) -> str:
        return "<RiverSegment X: {}, Y: {}, side: {}>".format(self.x, self.y, self.side)

    @property
    def size(self) -> int:
        """
        Gets the size of the rest of the river
        :return: Number
        """
        count = 1
        river = self
        while river.next is not None:
            count += 1
            river = river.next
        return count

    def __eq__(self, other: object) -> bool:
        """
        :param other: RiverSegment
        :return: True if both edges are equal
        """
        if not isinstance(other, RiverSegment):
            return NotImplemented
        return self.edge == other.edge  # type: bool

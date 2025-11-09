import sys
import random
from typing import Any, List, Dict, TYPE_CHECKING


sys.setrecursionlimit(1500)

if TYPE_CHECKING:
    from system.subsystems.hexgen.hex import Hex


class Territory:
    def __init__(self, grid: Any, main: "Hex", id_num: int, color: Any):
        self.grid: Any = grid
        self.id: int = id_num
        self.color: Any = color
        self.main: "Hex" = main  # main Hex
        main.territory = self
        self.last_added: List["Hex"] = [main]
        self.members: List["Hex"] = [main]  # Hexes part of this territory
        self.groups: List[Dict[Any, Any]] = []
        self.db_instance: Any = None

    @property
    def frontier(self) -> list[Any]:
        frontier: List["Hex"] = []
        for m in self.last_added:
            frontier.extend([h for h in m.surrounding if h.is_owned is False])
        return frontier

    @property
    def landlocked(self):
        for h in self.members:
            if any([h for h in h.surrounding if h.is_water]):
                return False
        return True

    @property
    def neighbors(self) -> set[Any]:
        terr: set["Territory"] = set()
        for h in self.members:
            terr.update(
                set(
                    [
                        m.territory
                        for m in h.surrounding
                        if m.is_land and m.territory is not None and m.territory.id != self.id
                    ]
                )
            )
        return terr

    def avg_temp(self):
        temperatures = [
            h.temperature if isinstance(h.temperature, (int, float)) else h.temperature[0] for h in self.members
        ]
        return round(sum(temperatures) / self.size, 2)

    @property
    def avg_moisture(self):
        return round(sum([h.moisture for h in self.members]) / self.size, 2)

    @property
    def biomes(self) -> List[Dict[str, Any]]:
        b: Dict[str, Dict[str, Any]] = {}
        for h in self.members:
            if h.biome.name in b:
                b[h.biome.name]["count"] += 1
            else:
                b[h.biome.name] = dict(biome=h.biome, count=1)
        return sorted(b.values(), key=lambda k: k["count"], reverse=True)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Territory):
            return NotImplemented
        return self.id == other.id

    def __key(self) -> tuple[int, Any]:
        return self.id, self.color

    def __hash__(self) -> int:
        return hash(self.__key())

    def __repr__(self) -> str:
        return "<Territory ID: {}>".format(self.id)

    def find_groups(self):
        def find_unmarked():
            while True:
                found = random.choice(self.members)
                if found.marked is False:
                    return found

        def step(sh: "Hex", group: List["Hex"]):
            if sh.marked:
                return
            else:
                sh.marked = True
                group.append(sh)

            sur = [
                s
                for s in sh.map_surrounding
                if s.is_land and s.territory is not None and s.territory == self and s.marked is False
            ]
            for h in sur:
                step(h, group)

        def num_marked():
            return len([h for h in self.members if h.marked])

        groups: List[List["Hex"]] = []
        while num_marked() < len(self.members):
            group: List["Hex"] = []
            sh = find_unmarked()
            step(sh, group)
            groups.append(group)

        result: List[Dict[str, Any]] = []
        for g in groups:
            mx_s = [h.x for h in g]
            mx = sum(mx_s) / len(mx_s)
            my_s = [h.y for h in g]
            my = sum(my_s) / len(my_s)
            result.append(dict(size=len(g), x=round(mx), y=round(my)))
        self.groups = result

    @property
    def size(self):
        return len(self.members)

from typing import List, Tuple


class Tiles:
    @staticmethod
    def get_directions_per_col(col: int = 0) -> List[Tuple[int, int]]:
        even, odd = Tiles.get_directions_dirs()
        if (col % 2) == 0:
            return even
        else:
            return odd

    @staticmethod
    def get_directions_dirs() -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        return [
            (+1, 0),  # face0
            (0, +1),  # face1
            (-1, 0),  # face2
            (-1, -1),  # face3
            (0, -1),  # face4
            (+1, -1),  # face5
        ], [
            (+1, +1),  # face0
            (0, +1),  # face1
            (-1, +1),  # face2
            (-1, 0),  # face3
            (0, -1),  # face4
            (+1, 0),  # face5
        ]

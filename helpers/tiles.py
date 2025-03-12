from gameplay.tiles.base_tile import BaseTile


class TileHelper:
    @staticmethod
    def hex_distance(tile1: BaseTile, tile2: BaseTile) -> int:
        """Calculate the hex grid distance between two tiles."""
        return (abs(tile1.x - tile2.x) + abs(tile1.y - tile2.y)) // 2

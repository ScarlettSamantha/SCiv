import random
from typing import TYPE_CHECKING, Dict, Tuple, Type

from gameplay.tiles.base_tile import BaseTile
from system.generators.base import BaseGenerator
from system.pyload import PyLoad

if TYPE_CHECKING:
    from system.game_settings import GameSettings


class RandomGenerator(BaseGenerator):
    NAME = "Random"
    DESCRIPTION = "Randomly generate a grid of hexagon tiles."

    def __init__(self, config: "GameSettings", base):
        super().__init__(config, base=base)
        self.config: "GameSettings" = config
        self.map: Dict[str, BaseTile] = self.world.map  # Syntax Sugar
        self.grid: Dict[Tuple[int, int], BaseTile] = self.world.grid  # Syntax Sugar

    def load_tiles(self):
        from gameplay.tiles.base_tile import BaseTile

        classes = PyLoad.load_classes("data/tiles", base_classes=BaseTile)
        if "Tile" in classes:
            del classes["Tile"]
        return classes

    def generate(self) -> bool:
        """Set up a grid of hexagon tiles with geometry-based collisions."""
        # Load and adjust the hex model.

        def generate_grid():
            tiles = self.load_tiles()
            for col in range(self.config.height):
                for row in range(self.config.width):
                    x = col * self.world.col_spacing
                    if col % 2 == 1:
                        y = row * self.world.row_spacing + (self.world.row_spacing * 0.5)
                    else:
                        y = row * self.world.row_spacing

                    tile: Type[BaseTile] = random.choice(list(tiles.values()))

                    obj_instance: BaseTile = tile(self.base, col, row, x, y)
                    obj_instance.render()
                    # Do after render to get the node. otherwise there is no tag to set..
                    self.map[
                        str(obj_instance.tag) if obj_instance.tag is None else obj_instance.generate_tag(col, row)
                    ] = obj_instance
                    self.grid[(col, row)] = obj_instance
                    self.map[str(obj_instance.tag)] = obj_instance

        generate_grid()
        self.place_starting_units()
        return True

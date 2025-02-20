from graphviz import render
from numpy import isin
from torch import rand
from os.path import join, dirname
from data.tiles.tile import Tile
from system.generators.base import BaseGenerator
from panda3d.core import BitMask32
from system.pyload import PyLoad
import random


class RandomGenerator(BaseGenerator):
    def __init__(self, config):
        self.config = config
        self.map = self.config.map  # Syntax Sugar
        self.grid = self.config.grid  # Syntax Sugar
        super().__init__(config)

    def load_tiles(self):
        from data.tiles.tile import Tile

        classes = PyLoad.load_classes("data/tiles", base_classes=Tile)
        if "Tile" in classes:
            del classes["Tile"]
        return classes

    def generate(self):
        """Set up a grid of hexagon tiles with geometry-based collisions."""
        # Load and adjust the hex model.

        tiles = self.load_tiles()
        for col in range(self.config.cols):
            for row in range(self.config.rows):
                x = col * self.config.col_spacing
                if col % 2 == 1:
                    y = row * self.config.row_spacing + (self.config.row_spacing * 0.5)
                else:
                    y = row * self.config.row_spacing

                tile: Tile = random.choice(list(tiles.values()))

                obj_instance: Tile = tile(self.config.base, col, row, x, y)
                obj_instance.render()
                # Do after render to get the node. otherwise there is no tag to set..
                self.map[obj_instance.tag] = obj_instance
                self.grid[(col, row)] = obj_instance

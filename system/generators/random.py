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
        hex_model = self.config.base.loader.loadModel("hex_tile.obj")
        hex_model.setScale(0.48)
        # Rotate the model so it lies flat.
        hex_model.setHpr(180, 90, 90)

        tiles = self.load_tiles()
        for col in range(self.config.cols):
            for row in range(self.config.rows):
                x = col * self.config.col_spacing
                if col % 2 == 1:
                    y = row * self.config.row_spacing + (self.config.row_spacing * 0.5)
                else:
                    y = row * self.config.row_spacing

                new_hex = hex_model.copyTo(self.config.base.render)

                new_hex.setPos(x, y, 0)

                # Give the render-geometry a collide mask so ray/solid can detect it
                new_hex.setCollideMask(BitMask32.bit(1))
                tag = f"tile_{col}_{row}"
                # Optionally, tag the tile for identification
                new_hex.setTag("tile_id", tag)

                # Remove the base tile model from the list of tiles

                tile = random.choice(list(tiles.values()))

                obj_instance: Tile = tile(tag, col, row, new_hex)
                color = obj_instance.color()
                if isinstance(color, tuple) and len(color) == 3:
                    color = color + (float(1),)
                texture_path = join(dirname(__file__), "../../", obj_instance.texture())
                texture = self.config.base.loader.loadTexture(texture_path)
                obj_instance.node.setTexture(texture)

                self.map[tag] = obj_instance
                self.grid[(col, row)] = obj_instance

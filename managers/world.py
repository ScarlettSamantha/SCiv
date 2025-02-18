from math import sqrt
from typing import Optional, Tuple, Dict
from panda3d.core import BitMask32
from mixins.singleton import Singleton
from data.tiles.tile import Tile

class World(Singleton):
    
    def __setup__(self, base):
        self.base = base
        self.hex_radius: float = 0.5
        self.col_spacing: float = 1.5
        self.cols: int = 5
        self.rows: int = 5
        self.middle_x: Optional[float] = None
        self.middle_y: Optional[float] = None
        self.map: Dict[str, Tile] = {}
        self.grid: Dict[Tuple[int, int], Tile] = {}
        
    def __init__(self, base):
        self.base = base

    def generate(self, cols: int, rows: int, radius: float, spacing: float = 1.5):
        self.hex_radius = radius  
        self.col_spacing = spacing * self.hex_radius
        self.row_spacing = sqrt(3) * self.hex_radius
        self.cols = cols
        self.rows = rows

        # Compute the middle of the grid.
        self.middle_x = ((cols - 1) * self.col_spacing) / 2.0
        self.middle_y = ((rows - 1) * self.row_spacing) / 2.0
    
    
    def setup_hex_tiles(self):
        """Set up a grid of hexagon tiles with geometry-based collisions."""
        # Load and adjust the hex model.
        hex_model = self.base.loader.loadModel("hex_tile.obj")
        hex_model.setScale(0.48)
        # Rotate the model so it lies flat.
        hex_model.setHpr(180, 90, 90)

        for col in range(self.cols):
            for row in range(self.rows):
                x = col * self.col_spacing
                if col % 2 == 1:
                    y = row * self.row_spacing + (self.row_spacing * 0.5)
                else:
                    y = row * self.row_spacing
                
                new_hex = hex_model.copyTo(self.base.render)
              
                new_hex.setPos(x, y, 0)

                # Give the render-geometry a collide mask so ray/solid can detect it
                new_hex.setCollideMask(BitMask32.bit(1))
                tag = f"tile_{col}_{row}"
                # Optionally, tag the tile for identification
                new_hex.setTag("tile_id", tag)
                
                obj_instance = Tile(tag, col, row, new_hex)
                
                self.map[tag] = obj_instance
                self.grid[(col, row)] = obj_instance
                
    def lookup(self, tag):
        return self.map[tag]
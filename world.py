from math import sqrt


def setup_hex_tiles(self):
        """Set up a grid of hexagon tiles."""
        hex_radius = 0.5  
        col_spacing = 1.5 * hex_radius
        row_spacing = sqrt(3) * hex_radius

        rows = 5
        cols = 5

        # Load and adjust the hex model.
        hex_model = self.loader.loadModel("hex_tile.obj")
        hex_model.setScale(0.48)
        # Rotate the model so it lies flat.
        hex_model.setHpr(180, 90, 90)

        for col in range(cols):
            for row in range(rows):
                x = col * col_spacing
                if col % 2 == 1:
                    y = row * row_spacing + (row_spacing * 0.5)
                else:
                    y = row * row_spacing
                new_hex = hex_model.copyTo(self.render)
                new_hex.setPos(x, y, 0)
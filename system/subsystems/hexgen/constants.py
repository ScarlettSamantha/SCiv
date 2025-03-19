import math
from PIL import ImageColor

HEXAGON_ANGLE = 28 * math.pi / 180;  # 30 degrees
SIDE_LENGTH = 17
BOARD_WIDTH = 100;
BOARD_HEIGHT = BOARD_WIDTH;
HEX_HEIGHT = math.sin(HEXAGON_ANGLE) * SIDE_LENGTH
HEX_RADIUS = math.cos(HEXAGON_ANGLE) * SIDE_LENGTH
HEX_RECT_HEIGHT = SIDE_LENGTH + 2 * HEX_HEIGHT
HEX_RECT_WIDTH = 2 * HEX_RADIUS


WORLD_TYPE_HEIGHT_RANGES = {
    1: (0, 255), # terran
    2: (0, 255), # barren
    3: (0, 0),   # gas
    4: (0, 100), # volcanic
    5: (0, 255), # oceanic
    6: (0, 100)  # glacial
}



# at or below these altitudes
TERRAIN_TERRAN = [
    (-25, (0, 15, 120)),
    (-15, (0, 20, 130)),
    (0,   (0, 20, 170)),
    (20,  (56, 89, 22)),
    (50,  (75, 112, 9)),
    (75,  (129, 135, 42)),
    (100, (196, 150, 95)),
    (110, (223, 190, 144)),
    (120, (233, 200, 154)),
    (135, (243, 210, 164)),
    (140, (253, 220, 174))
]

TERRAN_OCEAN_SATELLITE = [
    (-20, [(21, 51, 62), (20, 50, 61), (22, 52, 63)]),
    (-10, [(21, 61, 72), (20, 60, 71), (22, 62, 73)]),
    (0, [(31, 72, 80), (29, 70, 82), (33, 73, 79)])
]

VOLCANIC_LIQUID = [
    (217, 0, 0),
    (225, 0, 0),
    (200, 5, 5),
]

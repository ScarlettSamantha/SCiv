# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false

import sys
from pathlib import Path

from PyQt6.QtGui import QColor


SCRIPTS_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))


import worldgen_viewer_tool.palette as palette


def biome_color_for_key(value: str) -> QColor:
    return QColor(palette.biome_color_for_key(value))


def test_biome_color_for_flat_light_jungle_source_biome_is_green() -> None:
    assert biome_color_for_key("tropical_forest").name() == "#2f8f4e"


def test_biome_color_for_temperate_rainforest_uses_green_palette() -> None:
    assert biome_color_for_key("temperate_rainforest").name() == "#2f8f4e"

from typing import TYPE_CHECKING

from panda3d.core import AmbientLight, DirectionalLight, Vec4

if TYPE_CHECKING:
    from main import SCIV


def setup_lights(base: "SCIV"):
    # Ambient light.
    ambient_light = AmbientLight("ambient")
    ambient_light.setColor(Vec4(1, 1, 1, 1))
    ambient_light.setColorTemperature(6000)
    ambient_node = base.render.attachNewNode(ambient_light)

    # Directional light.
    directional_light = DirectionalLight("directional")
    directional_light.setColor(Vec4(1, 1, 1, 1))

    directional_node = base.render.attachNewNode(directional_light)
    directional_node.setHpr(45, -60, 0)

    base.render.setLight(ambient_node)
    # self.render.setLight(directional_node)

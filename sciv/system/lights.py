from typing import TYPE_CHECKING

from panda3d.core import AmbientLight, DirectionalLight, NodePath, Vec3, Vec4

if TYPE_CHECKING:
    from game import SCIV


def setup_lights(base: "SCIV"):
    # 1) Ambient fill so shadows aren’t pitch-black:
    ambient = AmbientLight("ambient")
    ambient.setColor(Vec4(1, 1, 1, 1))  # ~30% white
    ambient_np: NodePath = base.render.attachNewNode(ambient)  # type: ignore
    base.render.setLight(ambient_np)  # type: ignore

    # 2) “Sun” directional light for proper highlights/shadows:
    sun = DirectionalLight("sun")
    sun.setColor(Vec4(1.0, 1.0, 0.9, 1))  # full-strength, slight warmth
    sun.setShadowCaster(True, 1024, 1024)  # if you want shadows
    sun.setDirection(Vec3(-1, -1, -2))  # from above & behind
    sun_np: NodePath = base.render.attachNewNode(sun)  # type: ignore
    base.render.setLight(sun_np)  # type: ignore

from typing import TYPE_CHECKING

from panda3d.core import AmbientLight, NodePath, Vec4

if TYPE_CHECKING:
    from game import OpenCiv


def setup_lights(base: "OpenCiv"):
    # 1) Ambient fill so shadows aren’t pitch-black:
    ambient = AmbientLight("ambient")
    ambient.setColor(Vec4(1, 1, 1, 1))  # ~30% white
    ambient_np: NodePath = base.render.attachNewNode(ambient)  # type: ignore
    base.render.setLight(ambient_np)  # type: ignore

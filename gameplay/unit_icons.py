from typing import TYPE_CHECKING, Tuple, Dict, List

from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from panda3d.core import (
    CardMaker,
    NodePath,
    Shader,
    TextureStage,
    TransparencyAttrib,
    Texture,
    ColorBlendAttrib,
    LVecBase3f,
)

from helpers.cache import Cache

if TYPE_CHECKING:
    pass


class UnitIcons(DirectObject):
    def __init__(self, parent: NodePath) -> None:
        """
        Generic standing billboards for any unit icon.
        parent: scene node to attach icons under (typically render or a moving unit NodePath)
        """
        self.parent = parent

        # Cache of path -> Texture
        self._tex_cache: Dict[str, Texture] = {}
        # Each entry: (NodePath, base_world_pos: LVecBase3f, size: (w,h))
        self.markers: List[Tuple[NodePath, LVecBase3f, Tuple[float, float]]] = []

        # Hook our update into Panda3D's task manager
        self.base = Cache.get_showbase_instance()
        self.base.taskMgr.add(self._update_positions, "unit_icons_billboard_update")

    def _get_texture(self, path: str) -> Texture:
        """
        Load & cache the texture for a given virtual path.
        """
        if path in self._tex_cache:
            return self._tex_cache[path]

        tex = Cache.get_atlas().get_panda3d_texture_by_virtual_path(path)
        # mark as sRGB + alpha so gamma → linear happens correctly but alpha is unchanged
        tex.setFormat(Texture.F_srgb_alpha)  # type: ignore
        self._tex_cache[path] = tex
        return tex

    def add_marker(
        self,
        world_pos: Tuple[float, float, float],
        size: Tuple[float, float],
        texture_path: str,
    ) -> None:
        """
        Place one billboard at world_pos with given size (w,h) using the texture.
        world_pos: 3-tuple in render space
        size: (width, height) in world units
        """
        tex = self._get_texture(texture_path)

        # Create a unit-square quad centered at 0,0
        cm = CardMaker("marker_quad")
        cm.set_frame(-0.5, 0.5, -0.5, 0.5)  # type: ignore

        quad = self.base.render.attach_new_node(cm.generate())  # type: ignore

        # record the base world position and size
        x, y, z = world_pos
        z += 0.2
        pos = LVecBase3f(x, y, z)
        w, h = size
        self.markers.append((quad, pos, (w, h)))  # type: ignore

        # initial placement & scale
        quad.set_pos(pos)  # type: ignore
        quad.set_scale(w, h, 1)  # type: ignore

        # texture + transparency + blending
        ts = TextureStage("icon")
        quad.set_texture(ts, tex)  # type: ignore
        quad.setTransparency(TransparencyAttrib.MAlpha)  # type: ignore
        quad.setAttrib(  # type: ignore
            ColorBlendAttrib.make(  # type: ignore
                ColorBlendAttrib.MAdd,
                ColorBlendAttrib.OIncomingAlpha,
                ColorBlendAttrib.OOneMinusIncomingAlpha,
            )
        )

        # draw on top of opaque geometry
        quad.set_depth_write(True)  # type: ignore
        quad.set_depth_test(True)  # type: ignore
        quad.set_bin("transparent", 90)  # type: ignore

        # shader & uniforms
        quad.set_shader(  # type: ignore
            Shader.load(  # type: ignore
                Shader.SL_GLSL,
                "assets/shaders/unit_icon.vert",
                "assets/shaders/unit_icon.frag",
            )
        )
        quad.set_shader_input("billboard_position", pos)  # type: ignore
        quad.set_shader_input("size", LVecBase3f(w, h, 0))  # type: ignore
        quad.set_shader_input("iconTex", tex)  # type: ignore

        # always face camera
        quad.setBillboardPointEye()  # type: ignore

    def _update_positions(self, task: Task) -> Task:
        """
        Each frame, move & (re)scale each quad so it stays at its base_pos
        and keep its size when the camera zooms/rotates.
        """
        for quad, base_pos, (w, h) in self.markers:
            # (re)position
            quad.set_pos(base_pos)  # type: ignore
            # (re)scale
            quad.set_scale(w, 0, h)  # type: ignore
            # update the shader uniform too
            quad.set_shader_input("billboard_position", quad.get_pos(self.base.render))  # type: ignore
        return Task.cont  # type: ignore

    def remove_all(self) -> None:
        """
        Remove all billboards.
        """
        for quad, _, _ in self.markers:
            quad.remove_node()  # type: ignore
        self.markers.clear()

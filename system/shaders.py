from typing import Dict

from panda3d.core import Shader


class Shaders:
    def __init__(self):
        self.shaders: Dict[str, Shader] = {}

    def load_shader(self, name: str, vert_path: str, frag_path: str) -> Shader:
        shader = Shader.load(Shader.SL_GLSL, vert_path, frag_path)  # type: ignore
        self.shaders[name] = shader
        return shader  # type: ignore

    def get_shader(self, name: str) -> Shader | None:
        return self.shaders.get(name)

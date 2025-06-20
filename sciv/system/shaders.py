from typing import Dict

from panda3d.core import Shader  # type: ignore


class Shaders:
    def __init__(self):
        self.shaders: Dict[str, Shader] = {}

    def load_shader(self, name: str, vert_path: str, frag_path: str) -> Shader:  # type: ignore
        shader = Shader.load(Shader.SL_GLSL, vert_path, frag_path)  # type: ignore
        self.shaders[name] = shader  # type: ignore
        return shader  # type: ignore

    def get_shader(self, name: str) -> Shader | None:  # type: ignore
        return self.shaders.get(name)  # type: ignore

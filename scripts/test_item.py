from typing import Any

from kivy.app import App
from kivy.graphics import Color, InstructionGroup, Line
from kivy.graphics.texture import Texture
from kivy.uix.widget import Widget


class TestWidget(Widget):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)  # type: ignore
        # Create a trivial 2×2 white texture
        self.white_tex = Texture.create(size=(2, 2))  # type: ignore
        self.white_tex.blit_buffer(bytes([255, 255, 255, 255] * 4), colorfmt="rgba", bufferfmt="ubyte")  # type: ignore

        # Use an InstructionGroup to hold color & line
        instr = InstructionGroup()
        instr.add(Color(1, 1, 1, 1))  # Force white
        instr.add(Line(points=[50, 50, 200, 200], width=5, texture=self.white_tex))  # type: ignore

        with self.canvas:  # type: ignore
            self.canvas.add(instr)  # type: ignore


class TestApp(App):
    def build(self):
        return TestWidget()


if __name__ == "__main__":
    TestApp().run()

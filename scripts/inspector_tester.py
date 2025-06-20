from direct.showbase.ShowBase import ShowBase
from direct.showbase.BufferViewer import BufferViewer
from panda3d.core import loadPrcFileData
from panda3d_kivy.app import App as PKA
from kivy.uix.button import Button
from kivy.uix.widget import Widget


class KivyApp(PKA):
    def build(self) -> Widget:
        return Button(text="Hey")


class PandaKivyIntegration(ShowBase):
    def __init__(self) -> None:
        loadPrcFileData("", "show-frame-rate-meter 1")

        super().__init__()

        self.kivy_app: KivyApp = KivyApp(self)
        self.kivy_app.run()

        self.buffer_viewer: BufferViewer = BufferViewer(self.win, self)  #   type: ignore
        self.buffer_viewer.toggleEnable()

        render.explore()  # type: ignore  # noqa: F821


def main() -> None:
    app = PandaKivyIntegration()
    app.run()


if __name__ == "__main__":
    main()

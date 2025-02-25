#!/usr/bin/env python
from panda3d.core import loadPrcFileData
from direct.showbase.ShowBase import ShowBase
from panda3d_kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.dropdown import DropDown

# Optionally configure the window title
loadPrcFileData("", "window-title Simple Panda3D Window")


class Demo(App):
    def __init__(self, panda_app, **kwargs):
        super().__init__(panda_app, **kwargs)

    def build(self):
        layout = BoxLayout()
        layout.add_widget(Spinner(text="Hello", values=["World", "Panda3D", "Kivy"]))
        layout.add_widget(DropDown(text="Hello", values=["World", "Panda3D", "Kivy"]))
        return layout


class SimpleWindow(ShowBase):
    def __init__(self) -> None:
        ShowBase.__init__(self)

        # Create a Kivy App instance
        self.kivy_app = Demo(self)
        self.kivy_app.run()  # Starts the Kivy app


if __name__ == "__main__":
    app = SimpleWindow()
    app.run()  # Starts the main loop

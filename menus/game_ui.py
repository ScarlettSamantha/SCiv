from panda3d_kivy.app import App
from kivy.lang import Builder


KV = r"""
FloatLayout:

        # Action Bar below main panel
    BoxLayout:
        orientation: 'horizontal'
        size_hint: (0.2, 0.1)  # 40% width, 10% height
        pos_hint: {'x': 0, 'top': 0.5}  # Below the main panel
        padding: 10
        spacing: 10

        Button:
            text: "Action 1"
        Button:
            text: "Action 2"
        Button:
            text: "Action 3"

    # Top-left large panel
    BoxLayout:
        orientation: 'vertical'
        size_hint: (-1, 0)  # 40% width, 50% height
        pos_hint: {'x': 0, 'top': 1}  # Stick to the top-left
        padding: 10
        spacing: 10
        
        Label:
            text: "Main Panel"
            size_hint_y: None
            height: 50

    # Debug bar on the right, centered vertically
    BoxLayout:
        orientation: 'vertical'
        size_hint: (0.2, 0.4)  # 20% width, 40% height
        pos_hint: {'right': 1, 'center_y': 0.5}  # Right side, vertically centered
        padding: 10
        spacing: 10

        Label:
            text: "Debug Panel"
            size_hint_y: None
            height: 50

        Label:
            text: "Logs go here"
        Label:
            text: "FPS: 60"
"""


class GameUI(App):
    def __init__(self, panda_app, display_region=None, **kwargs):
        self.game_manager = kwargs.get("game_manager")
        del kwargs["game_manager"]
        super().__init__(panda_app, display_region, **kwargs)

    def build(self):
        # Build the Kivy UI from the KV string.
        return Builder.load_string(KV)

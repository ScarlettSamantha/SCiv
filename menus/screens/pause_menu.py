from distro import build_number
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem

KV = r"""
<PauseMenuScreen>:
    FloatLayout:
        canvas.before:
            Color:
                rgba: (0, 0, 0, 0.7)
            Rectangle:
                pos: self.pos
                size: self.size

        BoxLayout:
            orientation: 'vertical'
            size_hint: (0.4, 0.6)
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            padding: (40, 20)
            spacing: 15
            canvas.before:
                Color:
                    rgba: (0, 0, 0, 0.8)
                Rectangle:
                    pos: self.pos
                    size: self.size

            Button:
                text: "Continue"
                size_hint_y: None
                height: 50
                on_press: root.continue_game()
            Button:
                text: "Save"
                size_hint_y: None
                height: 50
            Button:
                text: "Load"
                size_hint_y: None
                height: 50
            Button:
                text: "Restart"
                size_hint_y: None
                height: 50
            Button:
                text: "Main Menu"
                size_hint_y: None
                height: 50
                on_press: root.manager.current = "main_menu"
            Button:
                text: "Quit"
                size_hint_y: None
                height: 50
                on_press: app.stop()
            Button:
                text: "Debug"
                size_hint_y: None
                height: 50
"""


class PauseMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Builder.load_string(KV)

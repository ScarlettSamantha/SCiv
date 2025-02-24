from distro import build_number
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem

KV = r"""
<OptionsScreen>:
    BoxLayout:
        orientation: 'vertical'
        TabbedPanel:
            do_default_tab: False

            TabbedPanelItem:
                text: "General"
                BoxLayout:
                    orientation: 'vertical'
                    Label:
                        text: "1.1 Language"
                    Spinner:
                        text: "English (en_EN)"
                        values: ["English (en_EN)", "Dutch (nl_NL)"]
                    Label:
                        text: "1.2 FPS Counter"
                    CheckBox:
                        id: fps_counter
                    Label:
                        text: "1.3 Mouse Lock"
                    CheckBox:
                        id: mouse_lock
                    Label:
                        text: "1.4 Build: " + str(app.build_number) + " | Version: " + str(app.version)

            TabbedPanelItem:
                text: "Video"
                BoxLayout:
                    orientation: 'vertical'
                    Label:
                        text: "2.1 Resolution"
                    Spinner:
                        text: "1080p"
                        values: ["900p (16:9)", "1080p (16:9)", "1440p (16:9)", "900p (16:10)", "1080p (16:10)", "1440p (16:10)", "2560x1080 (Ultrawide)", "3440x1440 (Ultrawide)"]
                    Label:
                        text: "2.2 Refresh Rate"
                    Slider:
                        min: 30
                        max: 144
                        step: 1
                    Label:
                        text: "2.3 Window Mode"
                    Spinner:
                        text: "Full Screen"
                        values: ["Full Screen", "Windowed", "Full Screen Windowed", "Duplicate"]
                    Label:
                        text: "Level of Details"
                    Spinner:
                        text: "Medium"
                        values: ["Low", "Medium", "High"]
                    Label:
                        text: "2.6 Graphics API: "
                    Spinner:
                        text: "OpenGL"
                        values: ["OpenGL", "DX8", "Vulkan (Experimental)"]

            TabbedPanelItem:
                text: "Developer"
                BoxLayout:
                    orientation: 'vertical'
                    CheckBox:
                        id: dev_mode
                    Label:
                        text: "3.1 Developer Mode"
                    CheckBox:
                        id: cheat_menu
                    Label:
                        text: "3.2 Cheat Menu"
                    Label:
                        text: "3.3 Git Commit: " + str(app.git_commit) + " | Panda3D: " + str(app.panda_version) + " | Kivy: " + str(app.kivy_version)
"""


class OptionsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.version = "v0.1.0-alpha"
        Builder.load_string(KV)

from typing import Optional

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.slider import Slider
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem

from main import Cache
from menus.kivy.elements.button_value import ButtonValue


class OptionsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.version = Cache.get_showbase_instance().version
        self.git_version: str = ""
        self.panda_version: str = ""
        self.kivy_version: str = ""

        self.selected_resolution = None

        self.layout: Optional[BoxLayout] = None
        self.add_widget(self.build_screen())

    def build_screen(self):
        layout = BoxLayout(orientation="vertical")
        tab_panel = TabbedPanel(do_default_tab=False)

        # General Tab
        general_tab = TabbedPanelItem(text="General")
        general_layout = BoxLayout(orientation="vertical")

        general_layout.add_widget(Label(text="1.1 Language"))

        # language_spinner = Spinner(text="English (en_EN)", values=["English (en_EN)", "Dutch (nl_NL)"])
        # general_layout.add_widget(language_spinner)

        general_layout.add_widget(Label(text="1.2 FPS Counter"))
        general_layout.add_widget(CheckBox())

        general_layout.add_widget(Label(text="1.3 Mouse Lock"))
        general_layout.add_widget(CheckBox())

        general_layout.add_widget(Label(text=f"1.4 Build: Unknown | Version: {self.version}"))
        general_tab.add_widget(general_layout)

        # Video Tab
        video_tab = TabbedPanelItem(text="Video")
        video_layout = BoxLayout(orientation="vertical")
        video_layout.add_widget(Label(text="2.1 Resolution"))

        grid = GridLayout(cols=3, size_hint=(1, None), height=200, spacing=5)
        resolutions = ["720p", "1080p", "1440p", "4K"]
        aspect_ratios = ["16:9", "16:10", "Ultrawide"]

        def select_resolution(button):
            if self.selected_resolution:
                self.selected_resolution.background_color = (1, 1, 1, 1)
            self.selected_resolution = button
            button.background_color = (0, 0, 1, 1)

        for res in resolutions:
            for aspect in aspect_ratios:
                resolution_value = (res, aspect)
                if res == "720p":
                    width, height = 1280, 720
                elif res == "1080p":
                    width, height = 1920, 1080
                elif res == "1440p":
                    width, height = 2560, 1440
                elif res == "4K":
                    width, height = 3840, 2160
                else:
                    width, height = 0, 0

                if aspect == "16:9":
                    aspect_ratio = 16 / 9
                elif aspect == "16:10":
                    aspect_ratio = 16 / 10
                elif aspect == "Ultrawide":
                    aspect_ratio = 21 / 9
                else:
                    aspect_ratio = 0

                resolution_value = (width, height, aspect_ratio)
                btn = ButtonValue(text=f"{res} {aspect}", value=resolution_value, size_hint=(1, None), height=40)
                btn.bind(on_release=lambda btn: select_resolution(btn))  # type: ignore
                grid.add_widget(btn)

        video_layout.add_widget(Label(text="2.1 Resolution"))
        video_layout.add_widget(grid)

        video_layout.add_widget(Label(text="2.2 Refresh Rate"))

        refresh_rate_slider = Slider(min=30, max=144, step=1)
        video_layout.add_widget(refresh_rate_slider)
        video_layout.add_widget(Label(text="2.3 Window Mode"))

        # window_mode_spinner = Spinner(
        #    text="Full Screen", values=["Full Screen", "Windowed", "Full Screen Windowed", "Duplicate"]
        # )
        # video_layout.add_widget(window_mode_spinner)

        video_layout.add_widget(Label(text="Level of Details"))
        # lod_spinner = Spinner(text="Medium", values=["Low", "Medium", "High"])
        # video_layout.add_widget(lod_spinner)

        # video_layout.add_widget(Label(text="2.6 Graphics API: "))
        # graphics_api_spinner = Spinner(text="OpenGL", values=["OpenGL", "DX8", "Vulkan (Experimental)"])

        # video_layout.add_widget(graphics_api_spinner)
        video_tab.add_widget(video_layout)

        # Developer Tab
        developer_tab = TabbedPanelItem(text="Developer")
        developer_layout = BoxLayout(orientation="vertical")
        developer_layout.add_widget(Label(text="3.1 Developer Mode"))
        developer_layout.add_widget(CheckBox())
        developer_layout.add_widget(Label(text="3.2 Cheat Menu"))
        developer_layout.add_widget(CheckBox())
        developer_layout.add_widget(
            Label(
                text=f"3.3 Git Commit: {self.git_version} | Panda3D: {self.panda_version} | Kivy: {self.kivy_version}"
            )
        )
        developer_tab.add_widget(developer_layout)

        # Adding Tabs to TabbedPanel
        tab_panel.add_widget(general_tab)
        tab_panel.add_widget(video_tab)
        tab_panel.add_widget(developer_tab)

        layout.add_widget(tab_panel)
        return layout

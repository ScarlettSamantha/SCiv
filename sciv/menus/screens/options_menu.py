from typing import Any, List, Optional, Tuple, Dict

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner

from game import Cache
from managers.config import ConfigManager, WINDOW_MODE_FULLSCREEN, WINDOW_MODE_BORDERLESS, WINDOW_MODE_WINDOW


class OptionsScreen(Screen):
    RESOLUTIONS: Dict[str, Tuple[int, int]] = {
        "640x480": (640, 480),
        "800x600": (800, 600),
        "1024x768": (1024, 768),
        "1280x720": (1280, 720),
        "1280x800": (1280, 800),
        "1280x1024": (1280, 1024),
        "1440x900": (1440, 900),
        "1680x1050": (1680, 1050),
        "1920x1080": (1920, 1080),
        "2560x1440": (2560, 1440),
        "3840x2160": (3840, 2160),
        "5120x1440": (5120, 1440),
        "5120x2160": (5120, 2160),
    }

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.base = Cache.get_showbase_instance()
        self.version = self.base.version
        self.git_version: str = self.base.commit
        self.panda_version: str = ""
        self.kivy_version: str = ""

        self.selected_resolution: Optional[Tuple[int, int]] = None

        # prepare tab contents
        self._build_general_tab()
        self._build_video_tab()
        self._build_developer_tab()

        # assemble
        self.add_widget(self.build_screen())

    def build_screen(self) -> BoxLayout:
        root = BoxLayout(orientation="vertical")

        # Top bar: tabs left, actions right
        top_bar = BoxLayout(size_hint_y=None, height=48, padding=5, spacing=5)
        tabs_box = BoxLayout()
        for name in ("General", "Video", "Developer"):
            btn = Button(text=name, size_hint_x=None, width=100)
            btn.bind(on_release=lambda inst, nm=name: self.switch_tab(nm))  # type: ignore
            tabs_box.add_widget(btn)

        actions_box = BoxLayout(size_hint_x=None, width=180, spacing=5)
        btn_cancel = Button(text="Cancel")
        btn_cancel.bind(on_release=self.on_cancel)  # type: ignore

        btn_save = Button(text="Save")
        btn_save.bind(on_release=self.on_save)  # type: ignore

        actions_box.add_widget(btn_cancel)
        actions_box.add_widget(btn_save)

        top_bar.add_widget(tabs_box)
        top_bar.add_widget(actions_box)
        root.add_widget(top_bar)

        # Content area
        self.content_area = BoxLayout()
        root.add_widget(self.content_area)

        # Default tab
        self.switch_tab("General")

        return root

    def switch_tab(self, name: str) -> None:
        self.content_area.clear_widgets()
        if name == "General":
            self.content_area.add_widget(self.general_layout)
        elif name == "Video":
            self.content_area.add_widget(self.video_layout)
        elif name == "Developer":
            self.content_area.add_widget(self.developer_layout)

    def on_cancel(self, *args: Any) -> None:
        # go back without saving
        if self.manager:
            self.manager.current = self.manager.previous()  #  type: ignore

    def on_save(self, *args: Any) -> None:
        fps = getattr(self, "fps_checkbox", None)
        mouse = getattr(self, "mouse_checkbox", None)

        # Video
        refresh = self.refresh_rate_slider.value
        window_mode = self.window_mode_spinner.text
        resolution = self.selected_resolution if self.selected_resolution else None
        # Developer

        dev = getattr(self, "dev_checkbox", None)  #  type: ignore
        cheat = getattr(self, "cheat_checkbox", None)  # type: ignore
        print(
            f"Saving Settings:\n FPS counter: {bool(fps.active) if fps else 'n/a'}"
            f"\n Mouse Lock: {bool(mouse.active) if mouse else 'n/a'}"
            f"\n Resolution: {resolution}"
            f"\n Refresh: {refresh}"
            f"\n Mode: {window_mode}"
        )
        # TODO: persist to Cache or config

    def _build_general_tab(self) -> None:
        self.general_layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.general_layout.add_widget(Label(text="1.1 Language"))
        # example spinner
        self.language_spinner = Spinner(
            text="English (en_EN)", values=["English (en_EN)", "Dutch (nl_NL)"], size_hint=(None, None), width=200
        )
        self.general_layout.add_widget(self.language_spinner)

        self.general_layout.add_widget(Label(text="1.2 FPS Counter"))
        self.fps_checkbox = CheckBox()
        self.general_layout.add_widget(self.fps_checkbox)

        self.general_layout.add_widget(Label(text="1.3 Mouse Lock"))
        self.mouse_checkbox = CheckBox()
        self.general_layout.add_widget(self.mouse_checkbox)

        self.general_layout.add_widget(Label(text=f"1.4 Build: Unknown | Version: {self.version}"))

    def _build_video_tab(self) -> None:
        self.video_layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.video_layout.add_widget(Label(text="2.1 Resolution"))

        resolution_options: List[str] = []
        for resolution in self.RESOLUTIONS:
            resolution_options.append(f"{resolution}")

        self.resolution_spinner = Spinner(
            text="Select Resolution", values=resolution_options, size_hint=(None, None), width=200
        )
        self.resolution_spinner.bind(text=self._on_resolution_select)
        self.video_layout.add_widget(self.resolution_spinner)

        self.video_layout.add_widget(Label(text="2.2 Refresh Rate"))
        self.refresh_rate_slider = Slider(min=30, max=144, step=1)
        self.video_layout.add_widget(self.refresh_rate_slider)

        self.video_layout.add_widget(Label(text="2.3 Window Mode"))
        self.window_mode_spinner = Spinner(
            text="Full Screen",
            values=["Full Screen", "Windowed", "Full Screen Windowed"],
            size_hint=(None, None),
            width=200,
        )
        self.video_layout.add_widget(self.window_mode_spinner)
        self.window_mode_spinner.bind(text=self._on_screenmode_select)

    def _on_resolution_select(self, spinner: Spinner, text: str) -> None:
        if text in self.RESOLUTIONS:
            self.selected_resolution = self.RESOLUTIONS[text]
        else:
            self.selected_resolution = None
        print(f"Selected resolution: {self.selected_resolution}")
        if self.selected_resolution is not None:
            ConfigManager.get_singleton_instance().set_resolution(*self.selected_resolution, auto_save=True)

    def _on_screenmode_select(self, spinner: Spinner, text: str) -> None:
        if text == "Full Screen":
            ConfigManager.get_singleton_instance().set_screen_mode(WINDOW_MODE_FULLSCREEN)
        elif text == "Windowed":
            ConfigManager.get_singleton_instance().set_screen_mode(WINDOW_MODE_WINDOW)
        elif text == "Full Screen Windowed":
            ConfigManager.get_singleton_instance().set_screen_mode(WINDOW_MODE_BORDERLESS)

    def _build_developer_tab(self) -> None:
        self.developer_layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.developer_layout.add_widget(Label(text="3.1 Developer Mode"))
        self.dev_checkbox = CheckBox()
        self.developer_layout.add_widget(self.dev_checkbox)

        self.developer_layout.add_widget(Label(text="3.2 Cheat Menu"))
        self.cheat_checkbox = CheckBox()
        self.developer_layout.add_widget(self.cheat_checkbox)

        self.developer_layout.add_widget(
            Label(
                text=(f"3.3 Git Commit: {self.git_version} | Panda3D: {self.panda_version} | Kivy: {self.kivy_version}")
            )
        )

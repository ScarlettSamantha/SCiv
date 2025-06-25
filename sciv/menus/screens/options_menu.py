from typing import Any, Optional, Tuple, Dict

from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

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
        "2560x1600": (2560, 1600),
        "3440x1440": (3440, 1440),
        "3840x2160": (3840, 2160),
        "5120x1440": (5120, 1440),
        "5120x2160": (5120, 2160),
    }

    LANGUAGES: Dict[str, str] = {
        "en_EN": "English (en_EN)",
        "nl_NL": "Nederlands (nl_NL)",
    }

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        from helpers.debug import Debug

        self.base = Cache.get_showbase_instance()
        self.version = self.base.version
        self.git_version: str = self.base.commit
        self.panda_version: str = Debug.get_panda_version()
        self.kivy_version: str = Debug.get_kivy_version()
        self.config_ref = ConfigManager.get_singleton_instance()
        self.version_text = (
            f"Git Commit: {self.git_version} | Panda3D: {self.panda_version} | Kivy: {self.kivy_version}"
        )

        self.selected_resolution: Optional[Tuple[int, int]] = None

        # prepare tab contents
        self._build_general_tab()
        self._build_video_tab()
        self._build_developer_tab()

        # assemble
        self.add_widget(self.build_screen())

    def _make_version_label(self):
        return Label(text=self.version_text, color=(0.8, 0.8, 0.8, 1), font_size="14sp", size_hint=(1, None), height=30)

    def build_screen(self) -> BoxLayout:
        root = BoxLayout(orientation="vertical")

        with root.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self._bg_rect = Rectangle(pos=(0, 0), size=(1, 1))
        root.bind(pos=self._update_bg, size=self._update_bg)

        top_bar = BoxLayout(size_hint_y=None, height=48, padding=5, spacing=5)
        tabs_box = BoxLayout()
        for name in ("General", "Video", "Developer"):
            btn = Button(text=name, size_hint_x=None, width=100)
            btn.bind(on_release=lambda _, nm=name: self.switch_tab(nm))  # type: ignore
            tabs_box.add_widget(btn)

        actions_box = BoxLayout(size_hint_x=None, width=180, spacing=5)
        btn_back = Button(text="Back")
        btn_back.bind(on_release=self.on_back)
        actions_box.add_widget(btn_back)

        top_bar.add_widget(tabs_box)
        top_bar.add_widget(actions_box)
        root.add_widget(top_bar)

        self.content_area = BoxLayout()
        root.add_widget(self.content_area)

        self.switch_tab("General")

        return root

    def _update_bg(self, instance: Widget, value: Tuple[float, float]) -> None:
        self._bg_rect.pos = instance.pos  # type: ignore
        self._bg_rect.size = instance.size

    def switch_tab(self, name: str) -> None:
        self.content_area.clear_widgets()
        if name == "General":
            self.content_area.add_widget(self.general_layout)
        elif name == "Video":
            self.content_area.add_widget(self.video_layout)
        elif name == "Developer":
            self.content_area.add_widget(self.developer_layout)

    def on_back(self, *args: Any) -> None:
        if self.manager:
            self.manager.current = "main_menu"

    def _build_general_tab(self) -> None:
        self.general_layout = BoxLayout(orientation="vertical", padding=10, spacing=20)

        self.general_layout.add_widget(Label(text="Language", font_size="18sp", bold=True, color=(1, 1, 1, 1)))
        self.language_spinner = Spinner(
            text=self.LANGUAGES.get(self.config_ref.get_language(), "English (en_EN)"),
            values=list(self.LANGUAGES.values()),
            size_hint=(None, None),
            width=200,
            pos_hint={"center_x": 0.5},
        )
        self.language_spinner.bind(text=self._on_language_select)
        self.general_layout.add_widget(self.language_spinner)

        self.general_layout.add_widget(Label(text="FPS Counter", font_size="18sp", bold=True, color=(1, 1, 1, 1)))
        self.fps_checkbox = CheckBox(size_hint=(None, None), size=(40, 40), pos_hint={"center_x": 0.5})
        self.fps_checkbox.bind(active=self._on_fps_toggle)
        self.general_layout.add_widget(self.fps_checkbox)

        self.general_layout.add_widget(Label(text="Mouse Lock", font_size="18sp", bold=True, color=(1, 1, 1, 1)))
        self.mouse_checkbox = CheckBox(size_hint=(None, None), size=(40, 40), pos_hint={"center_x": 0.5})
        self.general_layout.add_widget(self.mouse_checkbox)

        self.general_layout.add_widget(self._make_version_label())

    def _build_video_tab(self) -> None:
        self.video_layout = BoxLayout(orientation="vertical", padding=10, spacing=20)

        self.video_layout.add_widget(Label(text="Resolution", font_size="18sp", bold=True, color=(1, 1, 1, 1)))
        resolution_options = list(self.RESOLUTIONS.keys())
        current_resolution = self.config_ref.get_resolution()
        self.resolution_spinner = Spinner(
            text=f"{current_resolution[0]}x{current_resolution[1]}",
            values=resolution_options,
            size_hint=(None, None),
            width=200,
            pos_hint={"center_x": 0.5},
        )
        self.resolution_spinner.bind(text=self._on_resolution_select)
        self.video_layout.add_widget(self.resolution_spinner)

        self.video_layout.add_widget(Label(text="Refresh Rate (Hz)", font_size="18sp", bold=True, color=(1, 1, 1, 1)))
        hr_box = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)

        self.refresh_rate_slider = Slider(min=30, max=144, step=1)
        hr_box.add_widget(self.refresh_rate_slider)
        self.rate_label = Label(text=str(int(self.refresh_rate_slider.value)), size_hint=(None, None), size=(50, 40))
        hr_box.add_widget(self.rate_label)

        self.refresh_rate_slider.bind(value=lambda inst, val: setattr(self.rate_label, "text", str(int(val))))  # type: ignore
        self.video_layout.add_widget(hr_box)

        self.video_layout.add_widget(Label(text="Enable VSync", font_size="18sp", bold=True, color=(1, 1, 1, 1)))

        self.vsync_checkbox = CheckBox(size_hint=(None, None), size=(40, 40), pos_hint={"center_x": 0.5})
        self.vsync_checkbox.bind(active=self._on_vsync_toggle)
        self.video_layout.add_widget(self.vsync_checkbox)

        vsync_enabled = self.config_ref.get_by_key(("window", "sync-video"), False)

        self.vsync_checkbox.active = vsync_enabled
        self.refresh_rate_slider.disabled = vsync_enabled

        self.video_layout.add_widget(Label(text="Window Mode", font_size="18sp", bold=True, color=(1, 1, 1, 1)))
        current_display_mode = self.config_ref.get_screen_mode()
        self.window_mode_spinner = Spinner(
            text=current_display_mode,
            values=[WINDOW_MODE_FULLSCREEN, WINDOW_MODE_BORDERLESS, WINDOW_MODE_WINDOW],
            size_hint=(None, None),
            width=200,
            pos_hint={"center_x": 0.5},
        )
        self.window_mode_spinner.bind(text=self._on_screenmode_select)
        self.video_layout.add_widget(self.window_mode_spinner)
        self.video_layout.add_widget(self._make_version_label())

    def _build_developer_tab(self) -> None:
        self.developer_layout = BoxLayout(orientation="vertical", padding=10, spacing=20)

        self.developer_layout.add_widget(Label(text="Developer Mode", font_size="18sp", bold=True, color=(1, 1, 1, 1)))
        self.dev_checkbox = CheckBox(size_hint=(None, None), size=(40, 40), pos_hint={"center_x": 0.5})
        self.dev_checkbox.bind(active=self._on_developer_mode_toggle)
        self.developer_layout.add_widget(self.dev_checkbox)

        self.developer_layout.add_widget(Label(text="Cheat Menu", font_size="18sp", bold=True, color=(1, 1, 1, 1)))
        self.cheat_checkbox = CheckBox(size_hint=(None, None), size=(40, 40), pos_hint={"center_x": 0.5})
        self.developer_layout.add_widget(self.cheat_checkbox)

        self.developer_layout.add_widget(Label(text="Debug Enable", font_size="18sp", bold=True, color=(1, 1, 1, 1)))
        master = self.config_ref.get_by_key(("debug", "enable"), False)
        self.debug_enable_checkbox = CheckBox(
            active=master, size_hint=(None, None), size=(40, 40), pos_hint={"center_x": 0.5}
        )
        self.developer_layout.add_widget(self.debug_enable_checkbox)

        dbg_cfg = self.config_ref.get_by_key(("debug", "debugs"), {})
        keys = list(dbg_cfg.keys())
        rows = (len(keys) + 2) // 3
        grid = GridLayout(
            cols=3,
            spacing=(10, 10),
            size_hint_y=None,
            row_force_default=True,
            row_default_height=40,
        )
        grid.height = rows * 40 + (rows - 1) * 10
        self.debug_checkboxes: Dict[str, CheckBox] = {}
        for key in keys:
            cell = BoxLayout(orientation="horizontal", spacing=5)
            cb = CheckBox(active=dbg_cfg.get(key, False), disabled=not master)
            cb.bind(active=lambda inst, val, k=key: self.toggle_debug_flag(k, bool(val)))  # type: ignore
            self.debug_checkboxes[key] = cb
            cell.add_widget(cb)
            cell.add_widget(Label(text=key.replace("_", " ").title(), color=(1, 1, 1, 1)))
            grid.add_widget(cell)
        self.developer_layout.add_widget(grid)

        self.developer_layout.add_widget(
            Label(text="Disable AI Turn Processing", font_size="18sp", bold=True, color=(1, 1, 1, 1))
        )
        ai_off = self.config_ref.get_by_key(("debug", "disable_ai_turn_processing"), False)
        self.disable_ai_checkbox = CheckBox(
            active=ai_off, disabled=not master, size_hint=(None, None), size=(40, 40), pos_hint={"center_x": 0.5}
        )
        self.developer_layout.add_widget(self.disable_ai_checkbox)

        sentry_conf = self.config_ref.get_by_key(("debug", "sentry"), {})
        sentry_en = sentry_conf.get("enable", False)
        self.developer_layout.add_widget(Label(text="Sentry Enable", font_size="18sp", bold=True, color=(1, 1, 1, 1)))
        self.sentry_enable_checkbox = CheckBox(
            active=sentry_en, disabled=not master, size_hint=(None, None), size=(40, 40), pos_hint={"center_x": 0.5}
        )

        self.developer_layout.add_widget(self.sentry_enable_checkbox)
        self.developer_layout.add_widget(Label(text="Sentry DSN", font_size="18sp", bold=True, color=(1, 1, 1, 1)))
        dsn = sentry_conf.get("dsn", "")
        self.sentry_dsn_input = TextInput(
            text=dsn,
            multiline=False,
            disabled=not master or not sentry_en,
            size_hint=(1, None),
            height=40,
        )
        self.developer_layout.add_widget(self.sentry_dsn_input)

        self.debug_enable_checkbox.bind(active=self._on_debug_enable_toggle)
        self.sentry_enable_checkbox.bind(
            active=lambda inst, val: setattr(
                self.sentry_dsn_input, "disabled", not val or not self.debug_enable_checkbox.active
            )
        )

        self.developer_layout.add_widget(self._make_version_label())

    def toggle_debug_flag(self, flag: str, active: bool) -> None:
        self.config_ref.toggle_debug_flag(flag, active)

    def _on_language_select(self, spinner: Spinner, text: str) -> None:
        lang_code = next((code for code, name in self.LANGUAGES.items() if name == text), "en_EN")
        Cache.get_i18n_instance().set_current_language(lang_code)
        self.config_ref.set_language(lang_code, auto_save=True)

    def _on_fps_toggle(self, checkbox: CheckBox, active: bool) -> None:
        self.config_ref.set_fps_counter(active)

    def _on_developer_mode_toggle(self, checkbox: CheckBox, active: bool) -> None:
        self.config_ref.set_developer_mode(active)

    def _on_debug_enable_toggle(self, checkbox: CheckBox, active: bool) -> None:
        # enable/disable all debug-related controls, preserving their states
        for cb in self.debug_checkboxes.values():
            cb.disabled = not active
        self.disable_ai_checkbox.disabled = not active
        self.sentry_enable_checkbox.disabled = not active
        self.sentry_dsn_input.disabled = not active or not self.sentry_enable_checkbox.active

    def _on_vsync_toggle(self, checkbox: CheckBox, active: bool) -> None:
        cfg = self.config_ref
        if active:
            cfg.enable_vsync()
            self.refresh_rate_slider.disabled = True
        else:
            cfg.disable_vsync()
            self.refresh_rate_slider.disabled = False

    def _on_resolution_select(self, spinner: Spinner, text: str) -> None:
        if text in self.RESOLUTIONS:
            self.selected_resolution = self.RESOLUTIONS[text]
        else:
            self.selected_resolution = None
        if self.selected_resolution:
            self.config_ref.set_resolution(*self.selected_resolution, auto_save=True)

    def _on_screenmode_select(self, spinner: Spinner, text: str) -> None:
        cfg = self.config_ref
        if text == WINDOW_MODE_FULLSCREEN:
            cfg.set_screen_mode(WINDOW_MODE_FULLSCREEN)
        elif text == WINDOW_MODE_WINDOW:
            cfg.set_screen_mode(WINDOW_MODE_WINDOW)
        elif text == WINDOW_MODE_BORDERLESS:
            cfg.set_screen_mode(WINDOW_MODE_BORDERLESS)

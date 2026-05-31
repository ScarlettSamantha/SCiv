from typing import Any, Dict, Optional, Tuple

from direct.showbase.MessengerGlobal import messenger
from helpers.cache import Cache
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from managers.config import (
    WINDOW_MODE_BORDERLESS,
    WINDOW_MODE_FULLSCREEN,
    WINDOW_MODE_WINDOW,
    ConfigManager,
)
from menus.kivy.elements.menu_styled import (  # type: ignore
    DarkPanel,
    LeftAlignedLabel,
    MenuCheckbox,
    SecondaryButton,
    SectionLabel,
    TitleLabel,
)


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

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        from helpers.debug import Debug  # type: ignore

        self.base = Cache.get_showbase_instance()
        self.version = self.base.version
        self.git_version: str = self.base.commit
        self.panda_version: str = Debug.get_panda_version()
        self.kivy_version: str = Debug.get_kivy_version()
        self.config_ref = ConfigManager.get_singleton_instance()
        self.version_text = (
            f"Version: {self.version} | Git: {self.git_version} | "
            f"Panda3D: {self.panda_version} | Kivy: {self.kivy_version}"
        )

        self.selected_resolution: Optional[Tuple[int, int]] = None

        self.general_layout: BoxLayout
        self.video_layout: BoxLayout
        self.developer_layout: BoxLayout

        self.fps_checkbox: CheckBox
        self.mouse_checkbox: CheckBox
        self.confirm_exit_checkbox: CheckBox
        self.language_spinner: Spinner

        self.refresh_rate_slider: Slider
        self.rate_label: Label
        self.vsync_checkbox: CheckBox
        self.resolution_spinner: Spinner
        self.window_mode_spinner: Spinner

        self.dev_checkbox: CheckBox
        self.cheat_checkbox: CheckBox
        self.debug_enable_checkbox: CheckBox
        self.disable_ai_checkbox: CheckBox
        self.sentry_enable_checkbox: CheckBox
        self.ui_layout_drag_checkbox: CheckBox
        self.ui_layout_overlay_checkbox: CheckBox
        self.ui_layout_reset_button: Button
        self.sentry_dsn_input: TextInput
        self.debug_checkboxes: Dict[str, CheckBox] = {}

        self.content_area: BoxLayout
        self._tab_buttons: Dict[str, Button] = {}
        self._panel_container: BoxLayout
        self._root_bg_rect: Rectangle
        self.current_tab: str = "General"

        self._build_general_tab()
        self._build_video_tab()
        self._build_developer_tab()

        self.add_widget(self.build_screen())

    def _make_version_label(self) -> Label:
        label = LeftAlignedLabel(
            text=self.version_text,
            color=(0.8, 0.8, 0.8, 1),
            font_size="13sp",
            size_hint=(1, None),
            height=dp(28),
        )
        return label

    def build_screen(self) -> FloatLayout:
        root = FloatLayout()

        with root.canvas.before:  # type: ignore
            Color(0.02, 0.02, 0.04, 1.0)
            self._root_bg_rect = Rectangle(pos=root.pos, size=root.size)  # type: ignore

        root.bind(
            pos=lambda inst, val: self._update_root_bg(inst, val),  # type: ignore
            size=lambda inst, val: self._update_root_bg(inst, val),  # type: ignore
        )

        self._panel_container = DarkPanel(
            orientation="vertical",
            size_hint=(0.8, 0.8),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(dp(32), dp(24)),
            spacing=dp(16),
        )

        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            padding=(dp(16), dp(10)),
            spacing=dp(10),
        )
        title_label = TitleLabel(
            text="[b]Settings[/b]",
            size_hint_x=0.7,
        )

        header_right = BoxLayout(
            orientation="horizontal",
            size_hint_x=0.3,
            spacing=dp(10),
        )
        version_short = LeftAlignedLabel(
            text=f"{self.version}",
            font_size="14sp",
            color=(0.8, 0.8, 0.8, 1),
            halign="right",
        )

        btn_back = SecondaryButton(
            text="Back",
            size_hint=(None, 1),
            width=dp(110),
            font_size="16sp",
        )
        btn_back.bind(on_release=self.on_back)  # type: ignore

        header_right.add_widget(version_short)
        header_right.add_widget(btn_back)

        header.add_widget(title_label)
        header.add_widget(header_right)
        self._panel_container.add_widget(header)

        tab_bar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            padding=(dp(16), 0),
            spacing=dp(8),
        )

        for name in ("General", "Video", "Developer"):
            btn = Button(
                text=name,
                size_hint=(None, 1),
                width=dp(120),
                background_normal="",
            )
            btn.bind(on_release=lambda _, nm=name: self.switch_tab(nm))  # type: ignore
            self._tab_buttons[name] = btn
            tab_bar.add_widget(btn)

        self._panel_container.add_widget(tab_bar)

        separator = Widget(size_hint_y=None, height=dp(1))

        with separator.canvas.before:  # type: ignore
            Color(0.2, 0.2, 0.22, 1)
            sep_rect = Rectangle(pos=separator.pos, size=separator.size)  # type: ignore

        def _update_sep_rect(instance: Widget, _val: Tuple[float, float]) -> None:
            sep_rect.pos = instance.pos  # type: ignore
            sep_rect.size = instance.size  # type: ignore

        separator.bind(pos=_update_sep_rect, size=_update_sep_rect)  # type: ignore
        self._panel_container.add_widget(separator)

        self.content_area = BoxLayout(
            orientation="vertical",
            padding=(dp(24), dp(20)),
        )
        self._panel_container.add_widget(self.content_area)

        footer = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(32),
            padding=(dp(16), dp(4)),
        )
        footer.add_widget(self._make_version_label())
        self._panel_container.add_widget(footer)

        self.switch_tab("General")

        root.add_widget(self._panel_container)
        return root

    def _update_root_bg(self, instance: Widget, _value: Tuple[float, float]) -> None:
        self._root_bg_rect.pos = instance.pos
        self._root_bg_rect.size = instance.size

    def _set_tab_styles(self, active_name: str) -> None:
        for name, btn in self._tab_buttons.items():
            btn.background_normal = ""  # type: ignore
            if name == active_name:
                btn.background_color = (0.25, 0.4, 0.7, 1)
                btn.color = (1, 1, 1, 1)  # type: ignore
            else:
                btn.background_color = (0.15, 0.15, 0.16, 1)
                btn.color = (0.9, 0.9, 0.9, 1)  # type: ignore

    def switch_tab(self, name: str) -> None:
        self.current_tab = name
        self.content_area.clear_widgets()

        if name == "General":
            self.content_area.add_widget(self.general_layout)
        elif name == "Video":
            self.content_area.add_widget(self.video_layout)
        elif name == "Developer":
            self.content_area.add_widget(self.developer_layout)

        self._set_tab_styles(name)

    def on_back(self, *args: Any) -> None:
        if self.manager:
            self.manager.current = "main_menu"

    def _build_general_tab(self) -> None:
        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(18),
        )

        caption = SectionLabel(
            text="[b]General[/b]",
            markup=True,
            font_size="18sp",
            size_hint=(1, None),
            height=dp(32),
        )
        layout.add_widget(caption)

        rows = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
        )

        language_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        language_label = LeftAlignedLabel(
            text="Language (restart needed)",
            font_size="16sp",
            size_hint_x=0.6,
        )

        self.language_spinner = Spinner(
            text=self.LANGUAGES.get(self.config_ref.get_language(), "English (en_EN)"),
            values=list(self.LANGUAGES.values()),
            size_hint=(None, None),
            width=dp(260),
            height=dp(40),
        )
        self.language_spinner.bind(text=self._on_language_select)  # type: ignore

        language_row.add_widget(language_label)
        language_row.add_widget(self.language_spinner)
        rows.add_widget(language_row)

        fps_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        fps_label = LeftAlignedLabel(
            text="FPS Counter",
            font_size="16sp",
            size_hint_x=0.6,
        )

        self.fps_checkbox = MenuCheckbox()
        self.fps_checkbox.bind(active=self._on_fps_toggle)  # type: ignore

        fps_row.add_widget(fps_label)
        fps_row.add_widget(self.fps_checkbox)
        rows.add_widget(fps_row)

        mouse_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        mouse_label = LeftAlignedLabel(
            text="Mouse Lock (restart/refocus needed)",
            font_size="16sp",
            size_hint_x=0.6,
        )

        self.mouse_checkbox = MenuCheckbox()
        self.mouse_checkbox.active = self.config_ref.get_by_key(("ui", "mouse_lock"), False)
        self.mouse_checkbox.bind(active=self._on_mouse_lock_toggle)  # type: ignore

        mouse_row.add_widget(mouse_label)
        mouse_row.add_widget(self.mouse_checkbox)
        rows.add_widget(mouse_row)

        confirm_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        confirm_label = LeftAlignedLabel(
            text="Confirm Before Exit",
            font_size="16sp",
            size_hint_x=0.6,
        )

        confirm_default = bool(getattr(self.base, "confirm_exit", True))
        self.confirm_exit_checkbox = MenuCheckbox(
            active=confirm_default,
        )
        self.confirm_exit_checkbox.bind(active=self._on_confirm_exit_toggle)  # type: ignore

        confirm_row.add_widget(confirm_label)
        confirm_row.add_widget(self.confirm_exit_checkbox)
        rows.add_widget(confirm_row)

        layout.add_widget(rows)
        self.general_layout = layout

    def _build_video_tab(self) -> None:
        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(18),
        )

        caption = SectionLabel(
            text="[b]Video[/b]",
            markup=True,
            font_size="18sp",
            size_hint=(1, None),
            height=dp(32),
        )
        layout.add_widget(caption)

        rows = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
        )

        resolution_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        resolution_label = LeftAlignedLabel(
            text="Resolution",
            font_size="16sp",
            size_hint_x=0.6,
        )

        resolution_options = list(self.RESOLUTIONS.keys())
        current_resolution = self.config_ref.get_resolution()
        self.resolution_spinner = Spinner(
            text=f"{current_resolution[0]}x{current_resolution[1]}",
            values=resolution_options,
            size_hint=(None, None),
            width=dp(260),
            height=dp(40),
        )
        self.resolution_spinner.bind(text=self._on_resolution_select)  # type: ignore

        resolution_row.add_widget(resolution_label)
        resolution_row.add_widget(self.resolution_spinner)
        rows.add_widget(resolution_row)

        refresh_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        refresh_label = LeftAlignedLabel(
            text="Refresh Rate (Hz)",
            font_size="16sp",
            size_hint_x=0.6,
        )

        slider_box = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_x=0.4,
        )
        self.refresh_rate_slider = Slider(min=30, max=144, step=1)
        self.rate_label = Label(
            text=str(int(self.refresh_rate_slider.value)),
            size_hint=(None, None),
            size=(dp(50), dp(40)),
            halign="center",
            valign="middle",
        )
        self.rate_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))  # type: ignore
        self.refresh_rate_slider.bind(value=lambda inst, val: setattr(self.rate_label, "text", str(int(val))))  # type: ignore

        slider_box.add_widget(self.refresh_rate_slider)
        slider_box.add_widget(self.rate_label)

        refresh_row.add_widget(refresh_label)
        refresh_row.add_widget(slider_box)
        rows.add_widget(refresh_row)

        vsync_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        vsync_label = LeftAlignedLabel(
            text="Enable VSync",
            font_size="16sp",
            size_hint_x=0.6,
        )

        self.vsync_checkbox = MenuCheckbox()
        self.vsync_checkbox.bind(active=self._on_vsync_toggle)  # type: ignore

        vsync_row.add_widget(vsync_label)
        vsync_row.add_widget(self.vsync_checkbox)
        rows.add_widget(vsync_row)

        vsync_enabled = self.config_ref.get_by_key(("window", "sync-video"), False)
        self.vsync_checkbox.active = vsync_enabled
        self.refresh_rate_slider.disabled = vsync_enabled

        window_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        window_label = LeftAlignedLabel(
            text="Window Mode",
            font_size="16sp",
            size_hint_x=0.6,
        )

        current_display_mode = self.config_ref.get_screen_mode()
        self.window_mode_spinner = Spinner(
            text=current_display_mode,
            values=[WINDOW_MODE_FULLSCREEN, WINDOW_MODE_BORDERLESS, WINDOW_MODE_WINDOW],
            size_hint=(None, None),
            width=dp(260),
            height=dp(40),
        )
        self.window_mode_spinner.bind(text=self._on_screenmode_select)  # type: ignore

        window_row.add_widget(window_label)
        window_row.add_widget(self.window_mode_spinner)
        rows.add_widget(window_row)

        layout.add_widget(rows)
        self.video_layout = layout

    def _build_developer_tab(self) -> None:
        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(18),
        )

        caption = SectionLabel(
            text="[b]Developer[/b]",
            markup=True,
            font_size="18sp",
            size_hint=(1, None),
            height=dp(32),
        )
        layout.add_widget(caption)

        rows = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
        )

        dev_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        dev_label = LeftAlignedLabel(
            text="Developer Mode",
            font_size="16sp",
            size_hint_x=0.6,
        )

        self.dev_checkbox = MenuCheckbox()
        self.dev_checkbox.bind(active=self._on_developer_mode_toggle)  # type: ignore

        dev_row.add_widget(dev_label)
        dev_row.add_widget(self.dev_checkbox)
        rows.add_widget(dev_row)

        cheat_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        cheat_label = LeftAlignedLabel(
            text="Cheat Menu",
            font_size="16sp",
            size_hint_x=0.6,
        )

        self.cheat_checkbox = MenuCheckbox()
        cheat_row.add_widget(cheat_label)
        cheat_row.add_widget(self.cheat_checkbox)
        rows.add_widget(cheat_row)

        debug_master_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        debug_master_label = LeftAlignedLabel(
            text="Debug Enable",
            font_size="16sp",
            size_hint_x=0.6,
        )

        master = self.config_ref.get_debug_mode()
        self.debug_enable_checkbox = MenuCheckbox(
            active=master,
        )

        debug_master_row.add_widget(debug_master_label)
        debug_master_row.add_widget(self.debug_enable_checkbox)
        rows.add_widget(debug_master_row)

        ui_drag_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        ui_drag_label = LeftAlignedLabel(
            text="Enable UI Layout Dragging",
            font_size="16sp",
            size_hint_x=0.6,
        )

        self.ui_layout_drag_checkbox = MenuCheckbox(
            active=self.config_ref.get_ui_layout_drag_enabled(),
            disabled=not master,
        )
        self.ui_layout_drag_checkbox.bind(active=self._on_ui_layout_drag_toggle)  # type: ignore

        ui_drag_row.add_widget(ui_drag_label)
        ui_drag_row.add_widget(self.ui_layout_drag_checkbox)
        rows.add_widget(ui_drag_row)

        ui_overlay_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        ui_overlay_label = LeftAlignedLabel(
            text="Show UI Layout Overlay",
            font_size="16sp",
            size_hint_x=0.6,
        )

        self.ui_layout_overlay_checkbox = MenuCheckbox(
            active=self.config_ref.get_ui_layout_overlay_enabled(),
            disabled=not master,
        )
        self.ui_layout_overlay_checkbox.bind(active=self._on_ui_layout_overlay_toggle)  # type: ignore

        ui_overlay_row.add_widget(ui_overlay_label)
        ui_overlay_row.add_widget(self.ui_layout_overlay_checkbox)
        rows.add_widget(ui_overlay_row)

        ui_reset_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(44),
            spacing=dp(12),
        )
        ui_reset_label = LeftAlignedLabel(
            text="Reset Saved UI Layout",
            font_size="16sp",
            size_hint_x=0.6,
        )

        self.ui_layout_reset_button = SecondaryButton(
            text="Reset",
            size_hint=(None, None),
            width=dp(140),
            height=dp(40),
        )
        self.ui_layout_reset_button.disabled = not master
        self.ui_layout_reset_button.bind(on_release=self._on_ui_layout_reset)  # type: ignore

        ui_reset_row.add_widget(ui_reset_label)
        ui_reset_row.add_widget(self.ui_layout_reset_button)
        rows.add_widget(ui_reset_row)

        dbg_cfg = self.config_ref.get_by_key(("debug", "debugs"), {})
        keys = list(dbg_cfg.keys())
        rows_count = (len(keys) + 2) // 3

        grid = GridLayout(
            cols=3,
            spacing=(dp(10), dp(10)),
            size_hint_y=None,
            row_force_default=True,
            row_default_height=dp(40),
        )
        grid.height = rows_count * dp(40) + (rows_count - 1) * dp(10)

        for key in keys:
            cell = BoxLayout(orientation="horizontal", spacing=dp(5))
            cb = CheckBox(
                active=dbg_cfg.get(key, False),
                disabled=not master,
                size_hint=(None, None),
                size=(dp(24), dp(24)),
            )
            cb.bind(active=lambda inst, val, k=key: self.toggle_debug_flag(k, bool(val)))  # type: ignore
            self.debug_checkboxes[key] = cb

            lbl = LeftAlignedLabel(
                text=key.replace("_", " ").title(),
                color=(1, 1, 1, 1),
                font_size="14sp",
            )

            cell.add_widget(cb)
            cell.add_widget(lbl)
            grid.add_widget(cell)

        rows.add_widget(grid)

        ai_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        ai_label = LeftAlignedLabel(
            text="Disable AI Turn Processing",
            font_size="16sp",
            size_hint_x=0.6,
        )

        ai_off = self.config_ref.get_by_key(("debug", "disable_ai_turn_processing"), False)
        self.disable_ai_checkbox = MenuCheckbox(
            active=ai_off,
            disabled=not master,
        )

        ai_row.add_widget(ai_label)
        ai_row.add_widget(self.disable_ai_checkbox)
        rows.add_widget(ai_row)

        sentry_conf = self.config_ref.get_by_key(("debug", "sentry"), {})
        sentry_en = sentry_conf.get("enable", False)

        sentry_enable_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        sentry_enable_label = LeftAlignedLabel(
            text="Sentry Enable",
            font_size="16sp",
            size_hint_x=0.6,
        )

        self.sentry_enable_checkbox = MenuCheckbox(
            active=sentry_en,
            disabled=not master,
        )

        sentry_enable_row.add_widget(sentry_enable_label)
        sentry_enable_row.add_widget(self.sentry_enable_checkbox)
        rows.add_widget(sentry_enable_row)

        sentry_dsn_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
        )
        sentry_dsn_label = LeftAlignedLabel(
            text="Sentry DSN",
            font_size="16sp",
            size_hint_x=0.6,
        )

        dsn = sentry_conf.get("dsn", "")
        self.sentry_dsn_input = TextInput(
            text=dsn,
            multiline=False,
            disabled=not master or not sentry_en,
            size_hint=(1, None),
            height=dp(40),
        )

        sentry_dsn_row.add_widget(sentry_dsn_label)
        sentry_dsn_row.add_widget(self.sentry_dsn_input)
        rows.add_widget(sentry_dsn_row)

        self.debug_enable_checkbox.bind(active=self._on_debug_enable_toggle)  # type: ignore
        self.sentry_enable_checkbox.bind(
            active=lambda inst, val: setattr(
                self.sentry_dsn_input,
                "disabled",
                not val or not self.debug_enable_checkbox.active,
            )
        )  # type: ignore

        layout.add_widget(rows)
        self.developer_layout = layout

    def toggle_debug_flag(self, flag: str, active: bool) -> None:
        self.config_ref.toggle_debug_flag(flag, active)

    def _on_language_select(self, spinner: Spinner, text: str) -> None:
        lang_code = next((code for code, name in self.LANGUAGES.items() if name == text), "en_EN")
        Cache.get_i18n_instance().set_current_language(lang_code)
        self.config_ref.set_language(lang_code, auto_save=True)

    def _on_mouse_lock_toggle(self, checkbox: CheckBox, active: bool) -> None:
        self.config_ref.set_mouse_lock(active)
        if active:
            self.base.input_manager.activate_mouse_lock()
        else:
            self.base.input_manager.de_activate_mouse_lock()

    def _on_confirm_exit_toggle(self, checkbox: CheckBox, active: bool) -> None:
        setattr(self.base, "confirm_exit", active)

    def _on_fps_toggle(self, checkbox: CheckBox, active: bool) -> None:
        self.config_ref.set_fps_counter(active)

    def _on_developer_mode_toggle(self, checkbox: CheckBox, active: bool) -> None:
        self.config_ref.set_developer_mode(active)

    def _on_debug_enable_toggle(self, checkbox: CheckBox, active: bool) -> None:
        self.config_ref.set_debug_mode(active)
        for cb in self.debug_checkboxes.values():
            cb.disabled = not active
        self.disable_ai_checkbox.disabled = not active
        self.sentry_enable_checkbox.disabled = not active
        self.ui_layout_drag_checkbox.disabled = not active
        self.ui_layout_overlay_checkbox.disabled = not active
        self.ui_layout_reset_button.disabled = not active
        self.sentry_dsn_input.disabled = not active or not self.sentry_enable_checkbox.active
        self._notify_layout_debug_changed()

    def _on_ui_layout_drag_toggle(self, checkbox: CheckBox, active: bool) -> None:
        self.config_ref.set_ui_layout_drag_enabled(active)
        self._notify_layout_debug_changed()

    def _on_ui_layout_overlay_toggle(self, checkbox: CheckBox, active: bool) -> None:
        self.config_ref.set_ui_layout_overlay_enabled(active)
        self._notify_layout_debug_changed()

    def _on_ui_layout_reset(self, *args: Any) -> None:
        self.config_ref.reset_ui_layout_positions()
        self._notify_layout_debug_changed(reset_positions=True)

    def _notify_layout_debug_changed(self, reset_positions: bool = False) -> None:
        messenger.send("ui.update.ui.layout_debug_changed", [reset_positions])

    def _on_vsync_toggle(self, checkbox: CheckBox, active: bool) -> None:
        cfg: ConfigManager = self.config_ref
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
        cfg: ConfigManager = self.config_ref
        if text == WINDOW_MODE_FULLSCREEN:
            cfg.set_screen_mode(WINDOW_MODE_FULLSCREEN)
        elif text == WINDOW_MODE_WINDOW:
            cfg.set_screen_mode(WINDOW_MODE_WINDOW)
        elif text == WINDOW_MODE_BORDERLESS:
            cfg.set_screen_mode(WINDOW_MODE_BORDERLESS)

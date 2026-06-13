from typing import Any, Dict, Optional, Tuple, cast

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
        self._syncing_controls: bool = False
        self._monitor_label_to_id: Dict[str, str] = {}

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
        self.monitor_spinner: Spinner

        self.dev_checkbox: CheckBox
        self.cheat_checkbox: CheckBox
        self.debug_enable_checkbox: CheckBox
        self.disable_ai_checkbox: CheckBox
        self.sentry_enable_checkbox: CheckBox
        self.ui_layout_drag_checkbox: CheckBox
        self.ui_layout_overlay_checkbox: CheckBox
        self.ui_layout_reset_button: Button
        self.worldgen_export_checkbox: CheckBox
        self.worldgen_export_dir_input: TextInput
        self.worldgen_export_batch_spinner: Spinner
        self.sentry_dsn_input: TextInput
        self.debug_checkboxes: Dict[str, CheckBox] = {}

        self.content_area: BoxLayout
        self._tab_buttons: Dict[str, Button] = {}
        self._panel_container: BoxLayout
        self._root_bg_rect: Rectangle
        self.current_tab: str = "General"
        self._return_screen_name: str = "main_menu"
        self._reopen_pause_menu_on_back: bool = False

        self._build_general_tab()
        self._build_video_tab()
        self._build_developer_tab()

        self.add_widget(self.build_screen())
        self.refresh_from_config()

    def on_pre_enter(self, *args: Any) -> None:
        self.refresh_from_config()

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

    def configure_return_target(self, screen_name: str, reopen_pause_menu: bool = False) -> None:
        self._return_screen_name = screen_name or "main_menu"
        self._reopen_pause_menu_on_back = reopen_pause_menu

    def on_back(self, *args: Any) -> None:
        if self.manager is None:
            return

        self.manager.current = self._return_screen_name

        if self._reopen_pause_menu_on_back:
            messenger.send("ui.update.ui.show_pause")

        self.configure_return_target("main_menu")

    def _add_control_row(self, rows: BoxLayout, label_text: str, control: Widget, height: int = 40) -> None:
        row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(height),
            spacing=dp(12),
        )
        label = LeftAlignedLabel(
            text=label_text,
            font_size="16sp",
            size_hint_x=0.6,
        )
        row.add_widget(label)
        row.add_widget(control)
        rows.add_widget(row)

    def _build_general_tab(self) -> None:
        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(18),
        )
        layout.add_widget(
            SectionLabel(
                text="[b]General[/b]",
                markup=True,
                font_size="18sp",
                size_hint=(1, None),
                height=dp(32),
            )
        )

        rows = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
        )

        self.language_spinner = Spinner(
            text=self.LANGUAGES.get(self.config_ref.get_language(), "English (en_EN)"),
            values=list(self.LANGUAGES.values()),
            size_hint=(None, None),
            width=dp(260),
            height=dp(40),
        )
        self.language_spinner.bind(text=self._on_language_select)  # type: ignore
        self._add_control_row(rows, "Language (restart needed)", self.language_spinner)

        self.fps_checkbox = MenuCheckbox(active=self.config_ref.get_fps_counter())
        self.fps_checkbox.bind(active=self._on_fps_toggle)  # type: ignore
        self._add_control_row(rows, "FPS Counter", self.fps_checkbox)

        self.mouse_checkbox = MenuCheckbox(active=self.config_ref.get_mouse_lock())
        self.mouse_checkbox.bind(active=self._on_mouse_lock_toggle)  # type: ignore
        self._add_control_row(rows, "Mouse Lock (restart/refocus needed)", self.mouse_checkbox)

        self.confirm_exit_checkbox = MenuCheckbox(
            active=self.config_ref.get_confirm_exit(),
        )
        self.confirm_exit_checkbox.bind(active=self._on_confirm_exit_toggle)  # type: ignore
        self._add_control_row(rows, "Confirm Before Exit", self.confirm_exit_checkbox)

        layout.add_widget(rows)
        self.general_layout = layout

    def _build_video_tab(self) -> None:
        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(18),
        )
        layout.add_widget(
            SectionLabel(
                text="[b]Video[/b]",
                markup=True,
                font_size="18sp",
                size_hint=(1, None),
                height=dp(32),
            )
        )

        rows = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
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
        self._add_control_row(rows, "Resolution", self.resolution_spinner)

        current_rate = int(cast(int, self.config_ref.get_by_key(("render", "clock-frame-rate"), 60)))
        slider_box = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_x=0.4,
        )
        self.refresh_rate_slider = Slider(min=30, max=144, step=1, value=current_rate)
        self.rate_label = Label(
            text=str(int(self.refresh_rate_slider.value)),
            size_hint=(None, None),
            size=(dp(50), dp(40)),
            halign="center",
            valign="middle",
        )
        self.rate_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))  # type: ignore
        self.refresh_rate_slider.bind(value=self._on_refresh_rate_change)  # type: ignore
        slider_box.add_widget(self.refresh_rate_slider)
        slider_box.add_widget(self.rate_label)
        self._add_control_row(rows, "Refresh Rate (Hz)", slider_box)

        vsync_enabled = bool(self.config_ref.get_by_key(("window", "sync-video"), False))
        self.vsync_checkbox = MenuCheckbox(active=vsync_enabled)
        self.vsync_checkbox.bind(active=self._on_vsync_toggle)  # type: ignore
        self._add_control_row(rows, "Enable VSync", self.vsync_checkbox)
        self.refresh_rate_slider.disabled = vsync_enabled

        current_display_mode = self.config_ref.get_screen_mode()
        self.window_mode_spinner = Spinner(
            text=current_display_mode,
            values=[WINDOW_MODE_FULLSCREEN, WINDOW_MODE_BORDERLESS, WINDOW_MODE_WINDOW],
            size_hint=(None, None),
            width=dp(260),
            height=dp(40),
        )
        self.window_mode_spinner.bind(text=self._on_screenmode_select)  # type: ignore
        self._add_control_row(rows, "Window Mode", self.window_mode_spinner)

        monitor_values = self._get_monitor_spinner_values()
        self.monitor_spinner = Spinner(
            text=self.config_ref.get_monitor_label(),
            values=monitor_values,
            size_hint=(None, None),
            width=dp(420),
            height=dp(40),
        )
        self.monitor_spinner.bind(text=self._on_monitor_select)  # type: ignore
        self._add_control_row(rows, "Monitor", self.monitor_spinner)

        layout.add_widget(rows)
        self.video_layout = layout

    def _build_developer_tab(self) -> None:
        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(18),
        )
        layout.add_widget(
            SectionLabel(
                text="[b]Developer[/b]",
                markup=True,
                font_size="18sp",
                size_hint=(1, None),
                height=dp(32),
            )
        )

        rows = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
        )

        master = self.config_ref.get_debug_mode()

        self.dev_checkbox = MenuCheckbox(active=self.config_ref.get_developer_mode())
        self.dev_checkbox.bind(active=self._on_developer_mode_toggle)  # type: ignore
        self._add_control_row(rows, "Developer Mode", self.dev_checkbox)

        self.cheat_checkbox = MenuCheckbox(active=self.config_ref.get_cheat_menu())
        self.cheat_checkbox.bind(active=self._on_cheat_menu_toggle)  # type: ignore
        self._add_control_row(rows, "Cheat Menu", self.cheat_checkbox)

        self.debug_enable_checkbox = MenuCheckbox(
            active=master,
        )
        self._add_control_row(rows, "Debug Enable", self.debug_enable_checkbox)

        self.ui_layout_drag_checkbox = MenuCheckbox(
            active=self.config_ref.get_ui_layout_drag_enabled(),
            disabled=not master,
        )
        self.ui_layout_drag_checkbox.bind(active=self._on_ui_layout_drag_toggle)  # type: ignore
        self._add_control_row(rows, "Enable UI Layout Dragging", self.ui_layout_drag_checkbox)

        self.ui_layout_overlay_checkbox = MenuCheckbox(
            active=self.config_ref.get_ui_layout_overlay_enabled(),
            disabled=not master,
        )
        self.ui_layout_overlay_checkbox.bind(active=self._on_ui_layout_overlay_toggle)  # type: ignore
        self._add_control_row(rows, "Show UI Layout Overlay", self.ui_layout_overlay_checkbox)

        self.ui_layout_reset_button = SecondaryButton(
            text="Reset",
            size_hint=(None, None),
            width=dp(140),
            height=dp(40),
        )
        self.ui_layout_reset_button.disabled = not master
        self.ui_layout_reset_button.bind(on_release=self._on_ui_layout_reset)  # type: ignore
        self._add_control_row(rows, "Reset Saved UI Layout", self.ui_layout_reset_button, height=44)

        dbg_cfg = self.config_ref.get_debug_flags()
        keys = list(dbg_cfg.keys())
        rows_count = max(1, (len(keys) + 2) // 3)

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
                active=bool(dbg_cfg.get(key, False)),
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
        rows.add_widget(
            SectionLabel(
                text="[b]World Generation Exports[/b]",
                markup=True,
                font_size="16sp",
                size_hint=(1, None),
                height=dp(28),
            )
        )

        self.worldgen_export_checkbox = MenuCheckbox(
            active=self.config_ref.get_world_generation_export_enabled(),
            disabled=not master,
        )
        self.worldgen_export_checkbox.bind(active=self._on_world_generation_export_toggle)  # type: ignore
        self._add_control_row(rows, "Export Raw Generated Worlds", self.worldgen_export_checkbox)

        self.worldgen_export_dir_input = TextInput(
            text=self.config_ref.get_world_generation_export_dir(),
            multiline=False,
            disabled=not master,
            size_hint=(1, None),
            height=dp(40),
        )
        self.worldgen_export_dir_input.bind(focus=self._on_world_generation_export_dir_focus)  # type: ignore
        self._add_control_row(rows, "Export Folder", self.worldgen_export_dir_input)

        self.worldgen_export_batch_spinner = Spinner(
            text=str(self.config_ref.get_world_generation_export_batch_count()),
            values=[str(value) for value in range(1, 13)],
            size_hint=(None, None),
            width=dp(140),
            height=dp(40),
            disabled=not master,
        )
        self.worldgen_export_batch_spinner.bind(text=self._on_world_generation_export_batch_select)  # type: ignore
        self._add_control_row(rows, "Offline Batch Count", self.worldgen_export_batch_spinner)

        self.disable_ai_checkbox = MenuCheckbox(
            active=self.config_ref.get_disable_ai_turn_processing(),
            disabled=not master,
        )
        self.disable_ai_checkbox.bind(active=self._on_disable_ai_toggle)  # type: ignore
        self._add_control_row(rows, "Disable AI Turn Processing", self.disable_ai_checkbox)

        sentry_en = self.config_ref.get_sentry_enabled()
        self.sentry_enable_checkbox = MenuCheckbox(
            active=sentry_en,
            disabled=not master,
        )
        self._add_control_row(rows, "Sentry Enable", self.sentry_enable_checkbox)

        self.sentry_dsn_input = TextInput(
            text=self.config_ref.get_sentry_dsn(),
            multiline=False,
            disabled=not master or not sentry_en,
            size_hint=(1, None),
            height=dp(40),
        )
        self._add_control_row(rows, "Sentry DSN", self.sentry_dsn_input)

        self.debug_enable_checkbox.bind(active=self._on_debug_enable_toggle)  # type: ignore
        self.sentry_enable_checkbox.bind(active=self._on_sentry_enable_toggle)  # type: ignore
        self.sentry_dsn_input.bind(focus=self._on_sentry_dsn_focus)  # type: ignore

        layout.add_widget(rows)
        self.developer_layout = layout

    def _get_monitor_spinner_values(self) -> Tuple[str, ...]:
        options = self.config_ref.get_monitor_options()
        self._monitor_label_to_id = {label: monitor_id for monitor_id, label in options.items()}
        return tuple(options.values())

    def _refresh_monitor_spinner(self) -> None:
        values = self._get_monitor_spinner_values()
        self.monitor_spinner.values = values
        selected_label = self.config_ref.get_monitor_label()
        self.monitor_spinner.text = selected_label if selected_label in values else values[0]

    def refresh_from_config(self) -> None:
        self._syncing_controls = True
        try:
            lang_code = self.config_ref.get_language()
            self.language_spinner.text = self.LANGUAGES.get(lang_code, "English (en_EN)")
            self.fps_checkbox.active = self.config_ref.get_fps_counter()
            self.mouse_checkbox.active = self.config_ref.get_mouse_lock()
            self.confirm_exit_checkbox.active = self.config_ref.get_confirm_exit()

            current_resolution = self.config_ref.get_resolution()
            self.resolution_spinner.text = f"{current_resolution[0]}x{current_resolution[1]}"
            current_rate = int(cast(int, self.config_ref.get_by_key(("render", "clock-frame-rate"), 60)))
            self.refresh_rate_slider.value = current_rate
            self.rate_label.text = str(current_rate)
            vsync_enabled = bool(cast(bool, self.config_ref.get_by_key(("window", "sync-video"), False)))
            self.vsync_checkbox.active = vsync_enabled
            self.refresh_rate_slider.disabled = vsync_enabled
            self.window_mode_spinner.text = self.config_ref.get_screen_mode()
            self._refresh_monitor_spinner()

            master = self.config_ref.get_debug_mode()
            self.dev_checkbox.active = self.config_ref.get_developer_mode()
            self.cheat_checkbox.active = self.config_ref.get_cheat_menu()
            self.debug_enable_checkbox.active = master
            for key, cb in self.debug_checkboxes.items():
                cb.active = self.config_ref.get_debug_flag(key)
                cb.disabled = not master
            self.disable_ai_checkbox.active = self.config_ref.get_disable_ai_turn_processing()
            self.sentry_enable_checkbox.active = self.config_ref.get_sentry_enabled()
            self.ui_layout_drag_checkbox.active = self.config_ref.get_ui_layout_drag_enabled()
            self.ui_layout_overlay_checkbox.active = self.config_ref.get_ui_layout_overlay_enabled()
            self.worldgen_export_checkbox.active = self.config_ref.get_world_generation_export_enabled()
            self.worldgen_export_dir_input.text = self.config_ref.get_world_generation_export_dir()
            self.worldgen_export_batch_spinner.text = str(self.config_ref.get_world_generation_export_batch_count())
            self.sentry_dsn_input.text = self.config_ref.get_sentry_dsn()
            self._set_debug_dependant_controls_enabled(master)
            setattr(self.base, "confirm_exit", self.config_ref.get_confirm_exit())
        finally:
            self._syncing_controls = False

    def _set_debug_dependant_controls_enabled(self, active: bool) -> None:
        for cb in self.debug_checkboxes.values():
            cb.disabled = not active
        self.disable_ai_checkbox.disabled = not active
        self.sentry_enable_checkbox.disabled = not active
        self.ui_layout_drag_checkbox.disabled = not active
        self.ui_layout_overlay_checkbox.disabled = not active
        self.ui_layout_reset_button.disabled = not active
        self.worldgen_export_checkbox.disabled = not active
        self.worldgen_export_dir_input.disabled = not active
        self.worldgen_export_batch_spinner.disabled = not active
        self.sentry_dsn_input.disabled = not active or not self.sentry_enable_checkbox.active

    def toggle_debug_flag(self, flag: str, active: bool) -> None:
        if self._syncing_controls:
            return
        self.config_ref.toggle_debug_flag(flag, active)

    def _on_language_select(self, spinner: Spinner, text: str) -> None:
        if self._syncing_controls:
            return
        lang_code = next((code for code, name in self.LANGUAGES.items() if name == text), "en_EN")
        Cache.get_i18n_instance().set_current_language(lang_code)
        self.config_ref.set_language(lang_code, auto_save=True)

    def _on_mouse_lock_toggle(self, checkbox: CheckBox, active: bool) -> None:
        if self._syncing_controls:
            return
        self.config_ref.set_mouse_lock(active)
        if active:
            self.base.input_manager.activate_mouse_lock()
        else:
            self.base.input_manager.de_activate_mouse_lock()

    def _on_confirm_exit_toggle(self, checkbox: CheckBox, active: bool) -> None:
        if self._syncing_controls:
            return
        setattr(self.base, "confirm_exit", active)
        self.config_ref.set_confirm_exit(active)

    def _on_fps_toggle(self, checkbox: CheckBox, active: bool) -> None:
        if self._syncing_controls:
            return
        self.config_ref.set_fps_counter(active)

    def _on_developer_mode_toggle(self, checkbox: CheckBox, active: bool) -> None:
        if self._syncing_controls:
            return
        self.config_ref.set_developer_mode(active)

    def _on_cheat_menu_toggle(self, checkbox: CheckBox, active: bool) -> None:
        if self._syncing_controls:
            return
        self.config_ref.set_cheat_menu(active)

    def _on_debug_enable_toggle(self, checkbox: CheckBox, active: bool) -> None:
        if self._syncing_controls:
            return
        self.config_ref.set_debug_mode(active)
        setattr(self.base, "debug", active)
        self._set_debug_dependant_controls_enabled(active)
        self._notify_layout_debug_changed()

    def _on_disable_ai_toggle(self, checkbox: CheckBox, active: bool) -> None:
        if self._syncing_controls:
            return
        self.config_ref.set_disable_ai_turn_processing(active)

    def _on_sentry_enable_toggle(self, checkbox: CheckBox, active: bool) -> None:
        if self._syncing_controls:
            return
        self.config_ref.set_sentry_enabled(active)
        self.sentry_dsn_input.disabled = not active or not self.debug_enable_checkbox.active

    def _on_sentry_dsn_focus(self, text_input: TextInput, focused: bool) -> None:
        if self._syncing_controls or focused:
            return
        self.config_ref.set_sentry_dsn(text_input.text)
        text_input.text = self.config_ref.get_sentry_dsn()

    def _on_world_generation_export_toggle(self, checkbox: CheckBox, active: bool) -> None:
        if self._syncing_controls:
            return
        self.config_ref.set_world_generation_export_enabled(active)

    def _on_world_generation_export_dir_focus(self, text_input: TextInput, focused: bool) -> None:
        if self._syncing_controls or focused:
            return

        self.config_ref.set_world_generation_export_dir(text_input.text)
        text_input.text = self.config_ref.get_world_generation_export_dir()

    def _on_world_generation_export_batch_select(self, spinner: Spinner, text: str) -> None:
        if self._syncing_controls:
            return
        if not text.isdigit():
            spinner.text = str(self.config_ref.get_world_generation_export_batch_count())
            return

        self.config_ref.set_world_generation_export_batch_count(int(text))
        spinner.text = str(self.config_ref.get_world_generation_export_batch_count())

    def _on_ui_layout_drag_toggle(self, checkbox: CheckBox, active: bool) -> None:
        if self._syncing_controls:
            return
        self.config_ref.set_ui_layout_drag_enabled(active)
        self._notify_layout_debug_changed()

    def _on_ui_layout_overlay_toggle(self, checkbox: CheckBox, active: bool) -> None:
        if self._syncing_controls:
            return
        self.config_ref.set_ui_layout_overlay_enabled(active)
        self._notify_layout_debug_changed()

    def _on_ui_layout_reset(self, *args: Any) -> None:
        self.config_ref.reset_ui_layout_positions()
        self._notify_layout_debug_changed(reset_positions=True)

    def _notify_layout_debug_changed(self, reset_positions: bool = False) -> None:
        messenger.send("ui.update.ui.layout_debug_changed", [reset_positions])

    def _on_vsync_toggle(self, checkbox: CheckBox, active: bool) -> None:
        if self._syncing_controls:
            return
        cfg: ConfigManager = self.config_ref
        if active:
            cfg.enable_vsync()
            self.refresh_rate_slider.disabled = True
        else:
            cfg.disable_vsync()
            self.refresh_rate_slider.disabled = False

    def _on_refresh_rate_change(self, slider: Slider, value: float) -> None:
        self.rate_label.text = str(int(value))
        if self._syncing_controls or self.vsync_checkbox.active:
            return
        self.config_ref.set_framerate_cap(int(value))

    def _on_resolution_select(self, spinner: Spinner, text: str) -> None:
        if self._syncing_controls:
            return
        if text in self.RESOLUTIONS:
            self.selected_resolution = self.RESOLUTIONS[text]
        else:
            self.selected_resolution = None
        if self.selected_resolution:
            self.config_ref.set_resolution(*self.selected_resolution, auto_save=True)

    def _on_screenmode_select(self, spinner: Spinner, text: str) -> None:
        if self._syncing_controls:
            return
        cfg: ConfigManager = self.config_ref
        if text == WINDOW_MODE_FULLSCREEN:
            cfg.set_screen_mode(WINDOW_MODE_FULLSCREEN)
        elif text == WINDOW_MODE_WINDOW:
            cfg.set_screen_mode(WINDOW_MODE_WINDOW)
        elif text == WINDOW_MODE_BORDERLESS:
            cfg.set_screen_mode(WINDOW_MODE_BORDERLESS)
        self.refresh_from_config()

    def _on_monitor_select(self, spinner: Spinner, text: str) -> None:
        if self._syncing_controls:
            return

        monitor_id = self._monitor_label_to_id.get(text)
        if monitor_id is None:
            self.refresh_from_config()
            return

        self.config_ref.set_monitor(monitor_id, auto_save=True, apply_now=True)
        self.refresh_from_config()

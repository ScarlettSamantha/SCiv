from typing import Any, Dict, List, Optional, Tuple, Type

from gameplay import civilization
from gameplay.civilization import Civilization as BaseCivilization
from gameplay.leader import Leader as BaseLeader
from gameplay.repositories.civilization import Civilization
from gameplay.repositories.leader import Leader as LeaderRepository
from gameplay.rules import GameRules, get_game_rules
from helpers.cache import Cache
from kivy.graphics import Color, Rectangle  # type: ignore
from kivy.metrics import dp  # type: ignore
from kivy.uix.boxlayout import BoxLayout  # type: ignore
from kivy.uix.button import Button  # type: ignore
from kivy.uix.checkbox import CheckBox  # type: ignore
from kivy.uix.floatlayout import FloatLayout  # type: ignore
from kivy.uix.image import Image  # type: ignore
from kivy.uix.label import Label  # type: ignore
from kivy.uix.popup import Popup  # type: ignore
from kivy.uix.screenmanager import Screen  # type: ignore
from kivy.uix.textinput import TextInput  # type: ignore
from kivy.uix.widget import Widget  # type: ignore
from managers.i18n import Translation
from menus.kivy.elements.button_value import ButtonValue  # type: ignore
from menus.kivy.elements.clipping import ClippingScrollList  # type: ignore
from menus.kivy.elements.scrollable_popup import ScrollablePopup  # type: ignore
from menus.kivy.elements.menu_styled import (  # type: ignore
    DangerButton,
    DarkPanel,
    IconButton,
    LeftAlignedLabel,
    MenuCheckbox,
    PrimaryButton,
    SecondaryButton,
    SectionLabel,
    SubtitleLabel,
    TitleLabel,
)
from panda3d.core import Texture
from gameplay.repositories.generators import GeneratorRepository
from system.generators.base import BaseGenerator, GeneratorSetupField
from system.generators.basic import Basic


class GameConfigMenu(Screen):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.layout: Optional[FloatLayout] = None
        self.container: Optional[BoxLayout] = None

        self.player_panel: Optional[BoxLayout] = None
        self.options_panel: Optional[BoxLayout] = None
        self.options_scroll: Optional[ClippingScrollList] = None
        self.player_list_container: Optional[BoxLayout] = None
        self.dev_row: Optional[BoxLayout] = None
        self.barb_row: Optional[BoxLayout] = None
        self.teams_row: Optional[BoxLayout] = None
        self.rules_row: Optional[BoxLayout] = None

        self.title_label: Optional[Label] = None
        self.civ_popup: Optional[Popup] = None
        self.leader_popup: Optional[Popup] = None

        self.players_label: Optional[Label] = None
        self.add_player_button: Optional[Button] = None

        self.dev_mode: Optional[CheckBox] = None
        self.no_barbarians: Optional[CheckBox] = None
        self.no_teams: Optional[CheckBox] = None

        self.start: Optional[Button | Widget] = None
        self.back: Optional[Button | Widget] = None
        self.button_container: Optional[BoxLayout] = None

        self.size_section: Optional[BoxLayout] = None
        self.size_popup: Optional[ScrollablePopup] = None
        self.size_popup_button: Optional[Button] = None
        self.generator_section: Optional[BoxLayout] = None
        self.generator_popup_button: Optional[ButtonValue] = None
        self.generator_popup: Optional[ScrollablePopup] = None
        self.generator_description_label: Optional[Label] = None
        self.generator_option_rows: List[BoxLayout] = []

        self.selected_size: Optional[Tuple[int, int]] = None
        self.selected_civilization: Optional[Type[BaseCivilization]] = None
        self.selected_leader: Optional[Type[BaseLeader]] = None
        self.selected_generator: Optional[Type[BaseGenerator]] = None

        self.player_rows: List[Dict[str, Any]] = []
        self.active_civ_row: Optional[BoxLayout] = None
        self.active_leader_row: Optional[BoxLayout] = None
        self.player_count: int = 0

        self.rect: Optional[Rectangle] = None
        self._background_rect: Optional[Rectangle] = None

        self.rules_popup: Optional[Popup] = None
        self.rules_state: Dict[str, Any] = {}
        self.rules_checkboxes: Dict[str, CheckBox] = {}
        self.rules_int_inputs: Dict[str, TextInput] = {}
        self.rule_definitions: Dict[str, Dict[str, Any]] = {}
        self.generator_option_values: Dict[str, Any] = {}
        self.generator_option_buttons: Dict[str, ButtonValue] = {}

        rules_obj: GameRules = get_game_rules()
        self.rules_state = dict(rules_obj.get_rules())
        self.rule_definitions = rules_obj.get_rule_definitions()

        self.add_widget(self.build_screen())

    def build_screen(self) -> FloatLayout:
        float_layout = FloatLayout()
        self.layout = float_layout

        with float_layout.canvas.before:  # type: ignore
            Color(0.02, 0.02, 0.04, 1.0)
            self._background_rect = Rectangle(size=float_layout.size, pos=float_layout.pos)  # type: ignore

        def update_background(instance: Widget, _value: Any) -> None:
            if self._background_rect is not None:
                self._background_rect.size = instance.size  # type: ignore
                self._background_rect.pos = instance.pos  # type: ignore

        float_layout.bind(size=update_background, pos=update_background)  # type: ignore

        self.container = DarkPanel(
            orientation="vertical",
            size_hint=(0.8, 0.85),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(dp(32), dp(28)),
            spacing=dp(20),
        )

        header = BoxLayout(
            orientation="vertical",
            size_hint=(1.0, None),
            height=dp(100),
            spacing=dp(4),
            padding=(0, 0, 0, dp(4)),
        )

        self.title_label = TitleLabel(
            text=f"[b]{str(Translation('ui.player_ui.game_config.title'))}[/b]",
            size_hint=(1.0, None),
            height=dp(48),
        )
        subtitle_label = SubtitleLabel(
            text=str(Translation("ui.player_ui.game_config.sub_title")),
            size_hint=(1.0, None),
            height=dp(32),
        )

        header.add_widget(self.title_label)
        header.add_widget(subtitle_label)
        self.container.add_widget(header)

        body = BoxLayout(
            orientation="horizontal",
            spacing=dp(20),
            size_hint=(1.0, 1.0),
        )

        self.player_panel = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint=(0.5, 1.0),
        )

        header_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=dp(40),
            spacing=dp(10),
        )

        self.players_label = LeftAlignedLabel(
            text="Players: 0",
            size_hint=(1.0, 1.0),
            font_size="16sp",
        )

        self.add_player_button = IconButton(
            text=str(Translation("ui.player_ui.game_config.add_button")),
        )
        self.add_player_button.bind(on_release=lambda _instance: self.add_player_row())  # type: ignore

        header_row.add_widget(self.players_label)
        header_row.add_widget(self.add_player_button)

        self.player_list_container = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint=(1.0, 1.0),
        )

        columns_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=dp(30),
            spacing=dp(10),
        )

        player_header = SectionLabel(
            text=str(Translation("ui.player_ui.game_config.player")),
            size_hint=(0.25, 1.0),
        )
        icon_header_spacer = Widget(
            size_hint=(None, 1.0),
            width=dp(40),
        )
        civ_header = SectionLabel(
            text=str(Translation("ui.player_ui.game_config.civilization")),
            size_hint=(0.3, 1.0),
        )
        leader_header = SectionLabel(
            text=str(Translation("ui.player_ui.game_config.leader")),
            size_hint=(0.3, 1.0),
        )
        remove_header = Label(
            text="",
            size_hint=(0.15, 1.0),
        )

        columns_row.add_widget(player_header)
        columns_row.add_widget(icon_header_spacer)
        columns_row.add_widget(civ_header)
        columns_row.add_widget(leader_header)
        columns_row.add_widget(remove_header)

        self.player_panel.add_widget(header_row)
        self.player_panel.add_widget(columns_row)
        self.player_panel.add_widget(self.player_list_container)

        for _ in range(4):
            self.add_player_row()

        self.options_panel = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint=(0.5, 1.0),
        )

        options_title = SectionLabel(
            text=f"[b]{str(Translation('ui.player_ui.game_config.game_options'))}[/b]",
            size_hint=(1.0, None),
            height=dp(40),
            font_size="24sp",
            markup=True,
        )

        self.options_panel.add_widget(options_title)

        self.options_scroll = ClippingScrollList(
            size_hint=(1.0, 1.0),
            hide_partially_visible=True,
        )
        self.options_scroll.bar_width = 0
        self.options_panel.add_widget(self.options_scroll)

        self.size_section = BoxLayout(
            orientation="vertical",
            size_hint=(1.0, None),
            spacing=dp(5),
            padding=(0, dp(4), 0, 0),
        )
        self.size_section.bind(minimum_height=self.size_section.setter("height"))  # type: ignore
        size_label = SectionLabel(
            text=str(Translation("ui.player_ui.game_config.map_size")),
            size_hint=(1.0, None),
            height=dp(24),
        )
        self.size_section.add_widget(size_label)

        self.size_popup_button = ButtonValue(
            text="90x90",
            value=(90, 90),
            size_hint=(1.0, None),
            height=dp(48),
        )
        self.size_popup_button.bind(on_release=self.open_size_popup)  # type: ignore
        self.size_section.add_widget(self.size_popup_button)

        self.generator_section = BoxLayout(
            orientation="vertical",
            size_hint=(1.0, None),
            spacing=dp(5),
            padding=(0, dp(4), 0, 0),
        )
        self.generator_section.bind(minimum_height=self.generator_section.setter("height"))  # type: ignore

        generator_label = SectionLabel(
            text="Map generator",
            size_hint=(1.0, None),
            height=dp(24),
        )
        self.generator_section.add_widget(generator_label)

        self.generator_popup_button = ButtonValue(
            text=str(getattr(Basic, "NAME", "Basic")),
            value=Basic,
            size_hint=(1.0, None),
            height=dp(48),
        )
        self.generator_popup_button.bind(on_release=self.open_generator_popup)  # type: ignore
        self.generator_section.add_widget(self.generator_popup_button)

        self.generator_description_label = SubtitleLabel(
            text=str(getattr(Basic, "DESCRIPTION", "")),
            size_hint=(1.0, None),
            height=dp(36),
        )
        self.generator_section.add_widget(self.generator_description_label)

        self.dev_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=dp(40),
            spacing=dp(10),
        )

        dev_label = LeftAlignedLabel(
            text=str(Translation("ui.player_ui.game_config.developer_mode")),
            size_hint=(1.0, 1.0),
        )

        self.dev_mode = MenuCheckbox()

        self.dev_row.add_widget(dev_label)
        self.dev_row.add_widget(self.dev_mode)

        self.barb_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=dp(40),
            spacing=dp(10),
        )

        barb_label = LeftAlignedLabel(
            text=str(Translation("ui.player_ui.game_config.no_barbarians")),
            size_hint=(1.0, 1.0),
        )

        self.no_barbarians = MenuCheckbox()

        self.barb_row.add_widget(barb_label)
        self.barb_row.add_widget(self.no_barbarians)

        self.teams_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=dp(40),
            spacing=dp(10),
        )

        teams_label = LeftAlignedLabel(
            text=str(Translation("ui.player_ui.game_config.no_teams")),
            size_hint=(1.0, 1.0),
        )

        self.no_teams = MenuCheckbox()

        self.teams_row.add_widget(teams_label)
        self.teams_row.add_widget(self.no_teams)

        self.rules_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=dp(40),
            spacing=dp(10),
        )

        rules_label = LeftAlignedLabel(
            text=str(Translation("ui.player_ui.game_config.game_rules")),
            size_hint=(1.0, 1.0),
        )

        rules_button = SecondaryButton(
            text=str(Translation("ui.player_ui.game_config.configure_rules")),
            size_hint=(None, None),
            width=dp(160),
            height=dp(40),
            font_size="16sp",
        )
        rules_button.bind(on_release=self.open_rules_popup)  # type: ignore

        self.rules_row.add_widget(rules_label)
        self.rules_row.add_widget(rules_button)

        self._initialize_generator_selection()

        self.button_container = BoxLayout(
            size_hint=(1.0, None),
            height=dp(52),
            orientation="horizontal",
            spacing=dp(10),
        )

        def create_menu_button(text: str) -> Button:
            return PrimaryButton(text=text)

        self.back = create_menu_button(str(Translation("ui.player_ui.game_config.back_button")))
        self.back.on_press = self.back_to_main_menu
        self.button_container.add_widget(self.back)

        self.button_container.add_widget(Widget(size_hint_x=1.0))

        self.start = create_menu_button(str(Translation("ui.player_ui.game_config.start_game_button")))
        self.start.on_press = self.start_game
        self.button_container.add_widget(self.start)

        self.options_panel.add_widget(self.button_container)

        body.add_widget(self.player_panel)
        body.add_widget(self.options_panel)

        self.container.add_widget(body)
        float_layout.add_widget(self.container)
        return float_layout

    def add_player_row(self) -> None:
        if self.player_list_container is None:
            return

        max_players: int = 12
        if len(self.player_rows) >= max_players:
            return

        index: int = len(self.player_rows) + 1

        row = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=dp(40),
            spacing=dp(10),
        )

        label = LeftAlignedLabel(
            text=f"Player {index}",
            size_hint=(0.25, 1.0),
            font_size="16sp",
        )

        civ_icon = Image(
            source="",
            size_hint=(None, 1.0),
            width=dp(40),
            allow_stretch=True,
            keep_ratio=True,
            opacity=0.0,
        )

        civ_button = SecondaryButton(
            text=str(Translation("ui.player_ui.game_config.random")),
            size_hint=(0.3, 1.0),
            font_size="16sp",
        )
        civ_button.bind(on_release=lambda _instance, r=row: self.open_civilization_popup_for_row(r))  # type: ignore

        leader_button = SecondaryButton(
            text=str(Translation("ui.player_ui.game_config.random")),
            size_hint=(0.3, 1.0),
            font_size="16sp",
        )
        leader_button.bind(on_release=lambda _instance, r=row: self.open_leader_popup_for_row(r))  # type: ignore

        remove_button = DangerButton(
            text=str(Translation("ui.player_ui.game_config.remove_button")),
        )
        remove_button.bind(on_release=lambda _instance, r=row: self.remove_player_row(r))  # type: ignore

        row.add_widget(label)
        row.add_widget(civ_icon)
        row.add_widget(civ_button)
        row.add_widget(leader_button)
        row.add_widget(remove_button)

        self.player_list_container.add_widget(row)

        self.player_rows.append(
            {
                "row": row,
                "label": label,
                "civ_icon": civ_icon,
                "civ_dropdown": civ_button,
                "leader_dropdown": leader_button,
                "selected_civ": None,
                "selected_leader": None,
            }
        )

        self.player_count = len(self.player_rows)
        self._reindex_player_labels()
        self._update_players_label()

    def remove_player_row(self, row: BoxLayout) -> None:
        if self.player_list_container is None:
            return

        if len(self.player_rows) <= 1:
            return

        data = self._find_player_row_data(row)
        if data is None:
            return

        self.player_list_container.remove_widget(row)
        self.player_rows.remove(data)

        self.player_count = len(self.player_rows)
        self._reindex_player_labels()
        self._update_players_label()

        if self.active_civ_row is row:
            self.active_civ_row = None
        if self.active_leader_row is row:
            self.active_leader_row = None

    def _find_player_row_data(self, row: BoxLayout) -> Optional[Dict[str, Any]]:
        for data in self.player_rows:
            if data.get("row") is row:
                return data
        return None

    def _reindex_player_labels(self) -> None:
        for idx, data in enumerate(self.player_rows, start=1):
            label: Label = data["label"]
            label.text = f"Player {idx}"

    def _update_players_label(self) -> None:
        if self.players_label is not None:
            self.players_label.text = f"Players: {len(self.player_rows)}"

    def open_size_popup(self, _instance: Button) -> None:
        if self.size_popup is None:
            self.size_popup = ScrollablePopup(
                title=str(Translation("ui.player_ui.game_config.map_size")),
                on_select=self.select_size,  # type: ignore
                items={
                    "10x10 (Testing)": (10, 10),
                    "25x25 (UI test)": (25, 25),
                    "50x50 (Small)": (50, 50),
                    "50x90 (Small 16:9)": (50, 90),
                    "75x120 (Small 4:3)": (75, 120),
                    "90x150 (Medium 3:5)": (90, 150),
                    "100x100 (Medium)": (100, 100),
                    "120x180 (Large 4:3)": (120, 180),
                    "150x150 (Large)": (150, 150),
                    "200x200 (Dont use)": (200, 200),
                    "250x250 (Dont use)": (250, 250),
                },
            )
        self.size_popup.open()

    def open_civilization_popup_for_row(self, row: BoxLayout) -> None:
        self.active_civ_row = row
        self.open_civilization_popup(None)

    def open_civilization_popup(self, _instance: Optional[Button]) -> None:
        if self.civ_popup is None:
            kv_values: Dict[str, Type[civilization.Civilization]] = {}

            for civ in Civilization.all():
                kv_values[str(civ.name)] = civ

            self.civ_popup = ScrollablePopup(  # type: ignore
                str(Translation("ui.player_ui.game_config.civilizations")),
                kv_values,
                self.select_civilization,  # type: ignore
            )
        self.civ_popup.open()  # type: ignore

    def open_leader_popup_for_row(self, row: BoxLayout) -> None:
        self.active_leader_row = row

        data = self._find_player_row_data(row)
        if data is None:
            return

        civ_type: Optional[Type[BaseCivilization]] = data.get("selected_civ")
        if civ_type is None:
            return

        self.open_leader_popup(civ_type)

    def open_leader_popup(self, civilization_type: Type[BaseCivilization]) -> None:
        leaders: List[Type[BaseLeader]] = LeaderRepository.for_civilization(civilization_type)
        if not leaders:
            return

        items: Dict[str, Type[BaseLeader]] = {}
        for leader in leaders:
            _leader = leader()  # type: ignore
            items[str(_leader.get_name())] = leader

        self.leader_popup = ScrollablePopup(  # type: ignore
            str(Translation("ui.player_ui.game_config.leaders")),
            items,
            self.select_leader,  # type: ignore
        )
        self.leader_popup.open()  # type: ignore

    def select_size(self, size: str, value: Tuple[int, int]) -> None:
        self.selected_size = value
        if self.size_popup_button is not None:
            self.size_popup_button.text = size

    def _initialize_generator_selection(self) -> None:
        GeneratorRepository.cache_refresh()
        generators = GeneratorRepository.all()
        if not generators:
            self.apply_selected_generator(Basic)
            return

        default_generator = next(
            (
                generator
                for generator in generators
                if str(getattr(generator, "NAME", generator.__name__)).lower() == "dynamic worlds"
            ),
            next((generator for generator in generators if generator is Basic), generators[0]),
        )
        self.apply_selected_generator(default_generator)

    def open_generator_popup(self, _instance: Button) -> None:
        GeneratorRepository.cache_refresh()
        items: Dict[str, Type[BaseGenerator]] = {
            str(getattr(generator, "NAME", generator.__name__)): generator for generator in GeneratorRepository.all()
        }
        self.generator_popup = ScrollablePopup(
            title="Map generator",
            items=items,
            on_select=self.select_generator,  # type: ignore[arg-type]
            cols=2,
        )
        self.generator_popup.open()

    def select_generator(self, generator_name: str, value: Type[BaseGenerator] | None) -> None:
        generator_cls = value or Basic
        self.apply_selected_generator(generator_cls, generator_name)

    def apply_selected_generator(
        self,
        generator_cls: Type[BaseGenerator],
        display_name: Optional[str] = None,
    ) -> None:
        previous_generator = self.selected_generator
        self.selected_generator = generator_cls

        if previous_generator is generator_cls:
            self.generator_option_values = generator_cls.sanitize_setup_options(self.generator_option_values)
        else:
            self.generator_option_values = generator_cls.get_default_setup_options()

        if self.generator_popup_button is not None:
            self.generator_popup_button.text = display_name or str(getattr(generator_cls, "NAME", generator_cls.__name__))
            self.generator_popup_button.set_value(generator_cls)

        if self.generator_description_label is not None:
            self.generator_description_label.text = str(getattr(generator_cls, "DESCRIPTION", ""))

        self._rebuild_generator_options()

    def _rebuild_generator_options(self) -> None:
        if self.selected_generator is None:
            return

        self.generator_option_rows = []
        self.generator_option_buttons = {}

        fields = self.selected_generator.get_setup_fields()
        for field in fields:
            row = BoxLayout(
                orientation="vertical",
                size_hint=(1.0, None),
                height=dp(72),
                spacing=dp(4),
            )

            label = SectionLabel(
                text=field.label,
                size_hint=(1.0, None),
                height=dp(20),
            )

            current_value = self.generator_option_values.get(field.key, field.default)
            button = ButtonValue(
                text=self._generator_option_text(field, current_value),
                value=current_value,
                size_hint=(1.0, None),
                height=dp(44),
            )
            button.bind(on_release=lambda _instance, setup_field=field: self.open_generator_option_popup(setup_field))  # type: ignore

            row.add_widget(label)
            row.add_widget(button)
            self.generator_option_rows.append(row)

            self.generator_option_buttons[field.key] = button

        self._rebuild_options_scroll_content()

    def _rebuild_options_scroll_content(self) -> None:
        if self.options_scroll is None:
            return

        self.options_scroll.clear_widgets()

        widgets: List[Widget] = []
        if self.size_section is not None:
            widgets.append(self.size_section)
        if self.generator_section is not None:
            widgets.append(self.generator_section)

        widgets.extend(self.generator_option_rows)

        for row in (self.dev_row, self.barb_row, self.teams_row, self.rules_row):
            if row is not None:
                widgets.append(row)

        for widget in widgets:
            self.options_scroll.add_widget(widget)

    def _generator_option_text(self, field: GeneratorSetupField, value: Any) -> str:
        for label, option_value in field.choices:
            if option_value == value:
                return label
        return str(field.default)

    def open_generator_option_popup(self, field: GeneratorSetupField) -> None:
        items = {label: value for label, value in field.choices}
        popup = ScrollablePopup(
            title=field.label,
            items=items,
            on_select=lambda label, value, setup_field=field: self.select_generator_option(  # type: ignore[arg-type]
                setup_field,
                label,
                value,
            ),
            cols=2,
        )
        popup.open()

    def select_generator_option(self, field: GeneratorSetupField, label: str, value: Any) -> None:
        self.generator_option_values[field.key] = value

        button = self.generator_option_buttons.get(field.key)
        if button is not None:
            button.text = label
            button.set_value(value)

    def select_civilization(self, civilization_name: str, value: Type[BaseCivilization]) -> None:
        if self.active_civ_row is not None:
            data = self._find_player_row_data(self.active_civ_row)
            if data is not None:
                data["selected_civ"] = value

                civ_dropdown: Button = data["civ_dropdown"]
                civ_dropdown.text = civilization_name

                civ_icon_widget: Image = data["civ_icon"]

                civ = value()
                icon_texture: Texture = Cache.get_asset_archive().get_kivy_image_texture(civ.icon)

                civ_icon_widget.texture = icon_texture
                civ_icon_widget.opacity = 1.0

                data["selected_leader"] = None
                leader_dropdown: Button = data["leader_dropdown"]
                leader_dropdown.text = str(Translation("ui.player_ui.game_config.random"))

                if self.player_rows and data is self.player_rows[0]:
                    self.selected_civilization = value
                return

        self.selected_civilization = value

    def select_leader(self, leader_name: str, value: Type[BaseLeader]) -> None:
        if self.active_leader_row is None:
            return

        data = self._find_player_row_data(self.active_leader_row)
        if data is None:
            return

        data["selected_leader"] = value
        dropdown: Button = data["leader_dropdown"]
        dropdown.text = leader_name

        if self.player_rows and data is self.player_rows[0]:
            self.selected_leader = value

    def open_rules_popup(self, _instance: Button) -> None:
        if self.rules_popup is None:
            self.rules_popup = self._build_rules_popup()
        self._sync_rules_popup()
        self.rules_popup.open()  # type: ignore

    def _build_int_rule_row(
        self,
        key: str,
        label_text: str,
        min_value: int,
        max_value: int,
        step: int = 1,
    ) -> BoxLayout:
        row = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=dp(40),
            spacing=dp(10),
        )

        label = LeftAlignedLabel(
            text=label_text,
            size_hint=(0.6, 1.0),
        )

        minus_button = SecondaryButton(
            text=str(Translation("ui.player_ui.game_config.remove_button")),
            size_hint=(None, 1.0),
            width=dp(40),
        )

        current_value = int(self.rules_state.get(key, min_value))

        input_field = TextInput(
            text=str(current_value),
            multiline=False,
            input_filter="int",
            halign="center",
            size_hint=(None, 1.0),
            width=dp(60),
        )

        plus_button = SecondaryButton(
            text=str(Translation("ui.player_ui.game_config.add_button")),
            size_hint=(None, 1.0),
            width=dp(40),
        )

        def apply_value(raw_value: str) -> None:
            if raw_value == "":
                return

            try:
                value_int = int(raw_value)
            except ValueError:
                value_int = int(self.rules_state.get(key, min_value))

            if value_int < min_value:
                value_int = min_value

            if value_int > max_value:
                value_int = max_value

            self.rules_state[key] = value_int

            if input_field.text != str(value_int):
                input_field.text = str(value_int)

        def on_minus(_btn: Button) -> None:
            try:
                cur = int(input_field.text)
            except ValueError:
                cur = int(self.rules_state.get(key, min_value))
            apply_value(str(cur - step))

        def on_plus(_btn: Button) -> None:
            try:
                cur = int(input_field.text)
            except ValueError:
                cur = int(self.rules_state.get(key, min_value))
            apply_value(str(cur + step))

        def on_text_change(_field: TextInput, text: str) -> None:
            if text == "":
                return
            apply_value(text)

        minus_button.bind(on_release=on_minus)  # type: ignore
        plus_button.bind(on_release=on_plus)  # type: ignore
        input_field.bind(text=on_text_change)  # type: ignore

        row.add_widget(label)
        row.add_widget(minus_button)
        row.add_widget(input_field)
        row.add_widget(plus_button)

        self.rules_int_inputs[key] = input_field

        return row

    def _build_rules_popup(self) -> Popup:
        content = DarkPanel(
            orientation="vertical",
            padding=(dp(24), dp(20)),
            spacing=dp(12),
        )

        for key, meta in self.rule_definitions.items():
            rule_type = meta.get("type")
            label_text = meta.get("label") or key.replace("_", " ").capitalize()

            if rule_type == "int":
                min_value = int(meta.get("min", 0))
                max_value = int(meta.get("max", 100))
                step = int(meta.get("step", 1))
                row = self._build_int_rule_row(
                    key=key,
                    label_text=label_text,
                    min_value=min_value,
                    max_value=max_value,
                    step=step,
                )
                content.add_widget(row)
            elif rule_type == "bool":
                row = BoxLayout(
                    orientation="horizontal",
                    size_hint=(1.0, None),
                    height=dp(40),
                    spacing=dp(10),
                )

                label = LeftAlignedLabel(
                    text=label_text,
                    size_hint=(1.0, 1.0),
                )

                checkbox = MenuCheckbox()
                checkbox.active = bool(self.rules_state.get(key, False))
                checkbox.bind(
                    active=lambda _instance, value, k=key: self._on_rule_checkbox_change(k, value)  # type: ignore
                )

                row.add_widget(label)
                row.add_widget(checkbox)
                content.add_widget(row)

                self.rules_checkboxes[key] = checkbox

        button_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=dp(50),
            spacing=dp(10),
        )

        button_row.add_widget(Widget(size_hint_x=1.0))

        close_button = SecondaryButton(
            text=str(Translation("ui.player_ui.game_config.close_button")),
            size_hint=(None, None),
            width=dp(160),
            height=dp(40),
        )
        close_button.bind(on_release=lambda *_: self.rules_popup.dismiss() if self.rules_popup is not None else None)  # type: ignore

        button_row.add_widget(close_button)
        content.add_widget(button_row)

        popup = Popup(
            title=str(Translation("ui.player_ui.game_config.game_rules")),
            content=content,
            size_hint=(0.6, 0.7),
        )
        return popup

    def _on_rule_checkbox_change(self, key: str, active: bool) -> None:
        self.rules_state[key] = active

    def _sync_rules_popup(self) -> None:
        for key, checkbox in self.rules_checkboxes.items():
            value = bool(self.rules_state.get(key, False))
            if checkbox.active != value:
                checkbox.active = value

        for key, input_field in self.rules_int_inputs.items():
            try:
                value_int = int(self.rules_state.get(key, 0))
            except (TypeError, ValueError):
                value_int = 0
            text = str(value_int)
            if input_field.text != text:
                input_field.text = text

    def update_selected_size(self) -> None:
        if self.size_popup_button is None:
            raise AssertionError("Size popup button is not initialized")

        size = self.size_popup_button.text.split(" ")[0].split("x")
        self.selected_size = (int(size[0]), int(size[1]))

    def start_game(self) -> None:
        from direct.showbase.MessengerGlobal import messenger
        from kivy.clock import Clock

        if self.selected_size is None:
            self.update_selected_size()

        size: Tuple[int, int] = self.selected_size  # type: ignore

        players_config: List[Dict[str, Any]] = []
        civ_for_local: Optional[Type[BaseCivilization]] = None

        for index, data in enumerate(self.player_rows):
            civ_cls: Optional[Type[BaseCivilization]] = data.get("selected_civ")
            leader_cls: Optional[Type[BaseLeader]] = data.get("selected_leader")

            if civ_cls is None:
                civ_cls = Civilization.random(1)  # type: ignore

            if index == 0:
                civ_for_local = civ_cls

            players_config.append(
                {
                    "civilization": civ_cls,
                    "leader": leader_cls,
                    "is_human": index == 0,
                }
            )

        if civ_for_local is None:
            civ_for_local = Civilization.random(1)  # type: ignore

        civ: Type[BaseCivilization] | None = civ_for_local

        assert civ is not None, "No civilization selected for local player"

        self.player_count = len(players_config)
        players: int = int(self.player_count)

        options: Dict[str, Any] = {
            "dev_mode": bool(self.dev_mode.active) if self.dev_mode is not None else False,
            "no_barbarians": bool(self.no_barbarians.active) if self.no_barbarians is not None else False,
            "no_teams": bool(self.no_teams.active) if self.no_teams is not None else False,
        }

        rules: Dict[str, Any] = dict(self.rules_state)

        generator_cls: Type[BaseGenerator] = self.selected_generator or Basic
        generator_options: Dict[str, Any] = generator_cls.sanitize_setup_options(self.generator_option_values)

        start_config: Dict[str, Any] = {
            "options": options,
            "rules": rules,
            "players": players_config,
            "generator": {
                "class": generator_cls,
                "name": str(getattr(generator_cls, "NAME", generator_cls.__name__)),
                "options": generator_options,
            },
        }

        def send_start_signal(*_args: Any) -> None:
            messenger.send("system.game.start_load", [size, civ, players, start_config])

        Clock.schedule_once(send_start_signal, 0.01)  # type: ignore

    def back_to_main_menu(self) -> None:
        manager = self.manager
        if manager is None:
            return

        manager.current = "main_menu"

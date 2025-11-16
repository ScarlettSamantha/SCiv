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
from menus.kivy.elements.button_value import ButtonValue  # type: ignore
from menus.kivy.elements.scrollable_popup import ScrollablePopup  # type: ignore
from panda3d.core import Texture


class GameConfigMenu(Screen):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.layout: Optional[FloatLayout] = None
        self.container: Optional[BoxLayout] = None

        self.player_panel: Optional[BoxLayout] = None
        self.options_panel: Optional[BoxLayout] = None
        self.player_list_container: Optional[BoxLayout] = None

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

        self.selected_size: Optional[Tuple[int, int]] = None
        self.selected_civilization: Optional[Type[BaseCivilization]] = None
        self.selected_leader: Optional[Type[BaseLeader]] = None

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

        self.container = BoxLayout(
            orientation="vertical",
            size_hint=(0.8, 0.85),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=(dp(32), dp(28)),
            spacing=dp(20),
        )

        with self.container.canvas.before:  # type: ignore
            Color(0.08, 0.08, 0.12, 0.9)
            self.rect = Rectangle(size=self.container.size, pos=self.container.pos)  # type: ignore

        def update_rect(instance: Widget, _value: Any) -> None:
            if self.rect is not None:
                self.rect.size = instance.size  # type: ignore
                self.rect.pos = instance.pos  # type: ignore

        self.container.bind(size=update_rect, pos=update_rect)  # type: ignore

        header = BoxLayout(
            orientation="vertical",
            size_hint=(1.0, None),
            height=dp(100),
            spacing=dp(4),
            padding=(0, 0, 0, dp(4)),
        )

        self.title_label = Label(
            text="[b]Game Configuration[/b]",
            font_size="32sp",
            size_hint=(1.0, None),
            height=dp(48),
            markup=True,
            halign="left",
            valign="middle",
        )
        subtitle_label = Label(
            text="Set players, map size and rules before starting",
            font_size="16sp",
            size_hint=(1.0, None),
            height=dp(32),
            color=(0.75, 0.75, 0.8, 1.0),
            halign="left",
            valign="middle",
        )

        def _update_header_label(instance: Label, _value: Any) -> None:
            instance.text_size = instance.size  # type: ignore

        self.title_label.bind(size=_update_header_label)  # type: ignore
        subtitle_label.bind(size=_update_header_label)  # type: ignore

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

        self.players_label = Label(
            text="Players: 0",
            size_hint=(1.0, 1.0),
            font_size="16sp",
            halign="left",
            valign="middle",
        )

        def _update_players_label_size(instance: Label, _value: Any) -> None:
            instance.text_size = instance.size  # type: ignore

        self.players_label.bind(size=_update_players_label_size)  # type: ignore

        self.add_player_button = Button(
            text="+",
            size_hint=(None, None),
            width=dp(40),
            height=dp(40),
            background_normal="",
            background_down="",
            background_color=(0.32, 0.24, 0.12, 1.0),
            color=(1.0, 1.0, 1.0, 1.0),
            font_size="20sp",
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

        player_header = Label(
            text="Player",
            size_hint=(0.25, 1.0),
            font_size="16sp",
        )
        icon_header_spacer = Widget(
            size_hint=(None, 1.0),
            width=dp(40),
        )
        civ_header = Label(
            text="Civilization",
            size_hint=(0.3, 1.0),
            font_size="16sp",
        )
        leader_header = Label(
            text="Leader",
            size_hint=(0.3, 1.0),
            font_size="16sp",
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

        options_title = Label(
            text="[b]Game Options[/b]",
            size_hint=(1.0, None),
            height=dp(40),
            font_size="24sp",
            markup=True,
            halign="left",
            valign="middle",
        )

        def _update_options_title_size(instance: Label, _value: Any) -> None:
            instance.text_size = instance.size  # type: ignore

        options_title.bind(size=_update_options_title_size)  # type: ignore
        self.options_panel.add_widget(options_title)

        self.size_section = BoxLayout(
            orientation="vertical",
            size_hint=(1.0, None),
            spacing=dp(5),
            padding=(0, dp(4), 0, 0),
        )
        size_label = Label(
            text="Map Size",
            size_hint=(1.0, None),
            height=dp(24),
            font_size="16sp",
            halign="left",
            valign="middle",
        )

        def _update_size_label(instance: Label, _value: Any) -> None:
            instance.text_size = instance.size  # type: ignore

        size_label.bind(size=_update_size_label)  # type: ignore
        self.size_section.add_widget(size_label)

        self.size_popup_button = ButtonValue(
            text="90x90",
            value=(90, 90),
            size_hint=(1.0, None),
            height=dp(48),
        )
        self.size_popup_button.bind(on_release=self.open_size_popup)  # type: ignore
        self.size_section.add_widget(self.size_popup_button)

        self.options_panel.add_widget(self.size_section)

        dev_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=dp(40),
            spacing=dp(10),
        )

        dev_label = Label(
            text="Developer Mode",
            size_hint=(1.0, 1.0),
            halign="left",
            valign="middle",
        )

        def _update_dev_label(instance: Label, _value: Any) -> None:
            instance.text_size = instance.size  # type: ignore

        dev_label.bind(size=_update_dev_label)  # type: ignore

        self.dev_mode = CheckBox(
            size_hint=(None, None),
            size=(dp(28), dp(28)),
        )

        dev_row.add_widget(dev_label)
        dev_row.add_widget(self.dev_mode)
        self.options_panel.add_widget(dev_row)

        barb_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=dp(40),
            spacing=dp(10),
        )

        barb_label = Label(
            text="No Barbarians",
            size_hint=(1.0, 1.0),
            halign="left",
            valign="middle",
        )

        def _update_barb_label(instance: Label, _value: Any) -> None:
            instance.text_size = instance.size  # type: ignore

        barb_label.bind(size=_update_barb_label)  # type: ignore

        self.no_barbarians = CheckBox(
            size_hint=(None, None),
            size=(dp(28), dp(28)),
        )

        barb_row.add_widget(barb_label)
        barb_row.add_widget(self.no_barbarians)
        self.options_panel.add_widget(barb_row)

        teams_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=dp(40),
            spacing=dp(10),
        )

        teams_label = Label(
            text="No Teams",
            size_hint=(1.0, 1.0),
            halign="left",
            valign="middle",
        )

        def _update_teams_label(instance: Label, _value: Any) -> None:
            instance.text_size = instance.size  # type: ignore

        teams_label.bind(size=_update_teams_label)  # type: ignore

        self.no_teams = CheckBox(
            size_hint=(None, None),
            size=(dp(28), dp(28)),
        )

        teams_row.add_widget(teams_label)
        teams_row.add_widget(self.no_teams)
        self.options_panel.add_widget(teams_row)

        rules_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1.0, None),
            height=dp(40),
            spacing=dp(10),
        )

        rules_label = Label(
            text="Game Rules",
            size_hint=(1.0, 1.0),
            halign="left",
            valign="middle",
        )

        def _update_rules_label(instance: Label, _value: Any) -> None:
            instance.text_size = instance.size  # type: ignore

        rules_label.bind(size=_update_rules_label)  # type: ignore

        rules_button = Button(
            text="Configure…",
            size_hint=(None, None),
            width=dp(160),
            height=dp(40),
            background_normal="",
            background_down="",
            background_color=(0.18, 0.2, 0.26, 1.0),
            color=(1.0, 1.0, 1.0, 1.0),
            font_size="16sp",
        )
        rules_button.bind(on_release=self.open_rules_popup)  # type: ignore

        rules_row.add_widget(rules_label)
        rules_row.add_widget(rules_button)
        self.options_panel.add_widget(rules_row)

        self.options_panel.add_widget(Widget(size_hint_y=1.0))

        self.button_container = BoxLayout(
            size_hint=(1.0, None),
            height=dp(52),
            orientation="horizontal",
            spacing=dp(10),
        )

        def create_menu_button(text: str) -> Button:
            button = Button(
                text=text,
                size_hint=(None, None),
                height=dp(48),
                width=dp(200),
                font_size="18sp",
                background_normal="",
                background_down="",
                background_color=(0.18, 0.2, 0.26, 1.0),
                color=(1.0, 1.0, 1.0, 1.0),
            )
            button.disabled_color = (0.7, 0.7, 0.7, 0.6)  # type: ignore
            return button

        self.back = create_menu_button("Back")
        self.back.on_press = self.back_to_main_menu
        self.button_container.add_widget(self.back)

        self.button_container.add_widget(Widget(size_hint_x=1.0))

        self.start = create_menu_button("Start")
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

        label = Label(
            text=f"Player {index}",
            size_hint=(0.25, 1.0),
            font_size="16sp",
            halign="left",
            valign="middle",
        )

        def _update_player_label(instance: Label, _value: Any) -> None:
            instance.text_size = instance.size  # type: ignore

        label.bind(size=_update_player_label)  # type: ignore

        civ_icon = Image(
            source="",
            size_hint=(None, 1.0),
            width=dp(40),
            allow_stretch=True,
            keep_ratio=True,
            opacity=0.0,
        )

        civ_button = Button(
            text="Random",
            size_hint=(0.3, 1.0),
            background_normal="",
            background_down="",
            background_color=(0.18, 0.2, 0.26, 1.0),
            color=(1.0, 1.0, 1.0, 1.0),
            font_size="16sp",
        )
        civ_button.bind(on_release=lambda _instance, r=row: self.open_civilization_popup_for_row(r))  # type: ignore

        leader_button = Button(
            text="Random",
            size_hint=(0.3, 1.0),
            background_normal="",
            background_down="",
            background_color=(0.18, 0.2, 0.26, 1.0),
            color=(1.0, 1.0, 1.0, 1.0),
            font_size="16sp",
        )
        leader_button.bind(on_release=lambda _instance, r=row: self.open_leader_popup_for_row(r))  # type: ignore

        remove_button = Button(
            text="x",
            size_hint=(0.15, 1.0),
            background_normal="",
            background_down="",
            background_color=(0.32, 0.18, 0.18, 1.0),
            color=(1.0, 0.8, 0.8, 1.0),
            font_size="16sp",
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
                "Map sizes",
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
                "Civilizations",
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
            "Leaders",
            items,
            self.select_leader,  # type: ignore
        )
        self.leader_popup.open()  # type: ignore

    def select_size(self, size: str, value: Tuple[int, int]) -> None:
        self.selected_size = value
        if self.size_popup_button is not None:
            self.size_popup_button.text = size

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
                leader_dropdown.text = "Random"

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

        label = Label(
            text=label_text,
            size_hint=(0.6, 1.0),
            halign="left",
            valign="middle",
        )

        def _update_label(instance: Label, _value: Any) -> None:
            instance.text_size = instance.size  # type: ignore

        label.bind(size=_update_label)  # type: ignore

        minus_button = Button(
            text="-",
            size_hint=(None, 1.0),
            width=dp(40),
            background_normal="",
            background_down="",
            background_color=(0.18, 0.2, 0.26, 1.0),
            color=(1.0, 1.0, 1.0, 1.0),
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

        plus_button = Button(
            text="+",
            size_hint=(None, 1.0),
            width=dp(40),
            background_normal="",
            background_down="",
            background_color=(0.18, 0.2, 0.26, 1.0),
            color=(1.0, 1.0, 1.0, 1.0),
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
        content = BoxLayout(
            orientation="vertical",
            padding=(dp(24), dp(20)),
            spacing=dp(12),
        )

        with content.canvas.before:  # type: ignore
            Color(0.08, 0.08, 0.12, 0.95)
            bg_rect = Rectangle(size=content.size, pos=content.pos)  # type: ignore

        def _update_content_rect(instance: Widget, _value: Any) -> None:
            bg_rect.size = instance.size  # type: ignore
            bg_rect.pos = instance.pos  # type: ignore

        content.bind(size=_update_content_rect, pos=_update_content_rect)  # type: ignore

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

                label = Label(
                    text=label_text,
                    size_hint=(1.0, 1.0),
                    halign="left",
                    valign="middle",
                )

                def _update_bool_label(instance: Label, _value: Any) -> None:
                    instance.text_size = instance.size  # type: ignore

                label.bind(size=_update_bool_label)  # type: ignore

                checkbox = CheckBox(
                    size_hint=(None, None),
                    size=(dp(28), dp(28)),
                )
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

        close_button = Button(
            text="Close",
            size_hint=(None, None),
            width=dp(160),
            height=dp(40),
            background_normal="",
            background_down="",
            background_color=(0.18, 0.2, 0.26, 1.0),
            color=(1.0, 1.0, 1.0, 1.0),
        )
        close_button.bind(on_release=lambda *_: self.rules_popup.dismiss() if self.rules_popup is not None else None)  # type: ignore

        button_row.add_widget(close_button)
        content.add_widget(button_row)

        popup = Popup(
            title="Game Rules",
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

        start_config: Dict[str, Any] = {
            "options": options,
            "rules": rules,
            "players": players_config,
        }

        def send_start_signal(*_args: Any) -> None:
            messenger.send("system.game.start_load", [size, civ, players, start_config])

        Clock.schedule_once(send_start_signal, 0.01)  # type: ignore

    def back_to_main_menu(self) -> None:
        self.manager.current = "main_menu"

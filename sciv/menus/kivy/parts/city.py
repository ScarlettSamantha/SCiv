import weakref
from math import floor
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from gameplay.city import City
from gameplay.repositories.improvements import BaseCityImprovement
from gameplay.repositories.unit import UnitRepository
from gameplay.units.core.classes.civilian._base import CivilianBaseClass
from gameplay.units.core.classes.military._base import MilitaryBaseClass
from gameplay.yields import Yields
from helpers.debug import Debug
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from managers.i18n import t_
from menus.kivy.elements.button_value import ButtonValue
from menus.kivy.elements.clipping import ClippingScrollList
from menus.kivy.elements.image_label import ImageLabel

if TYPE_CHECKING:
    from game import OpenCiv
    from menus.screens.game_ui import GameUIScreen


class CityUI(BoxLayout, DirectObject):
    bg_rgba = ListProperty([0.0, 0.0, 0.0, 0.7])

    def __init__(
        self,
        base: "OpenCiv",
        screen: "GameUIScreen",
        name: str,
        background_color: Tuple[int, int, int, int] = (0, 0, 0, 0),
        border: Tuple[int, int, int, int] = (0, 0, 0, 0),
        **kwargs: Any,
    ):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("pos_hint", {"x": 0, "top": 0.982})
        kwargs.setdefault("pos", (dp(0), dp(100)))
        kwargs.setdefault("width", dp(400))
        kwargs.setdefault("height", dp(835))
        kwargs.setdefault("orientation", "vertical")

        super().__init__(**kwargs)  # type: ignore

        self.ref_screen: weakref.ReferenceType[GameUIScreen] = weakref.ref(screen)
        self.base: "OpenCiv" = base
        self.logger = base.logger.gameplay.getChild("ui.city_ui")

        self.background_color = background_color
        self.border = border
        self.background_image = None

        self.hidden: bool = False
        self.is_open: bool = False

        self.city_name = name
        self.city: Optional[City] = None

        self.city_label: Optional[Label] = None
        self.population_label: Optional[Label] = None
        self.is_capital_label: Optional[Label] = None
        self.tiles_label: Optional[Label] = None
        self.player_label: Optional[Label] = None
        self.current_button: Optional[Button] = None
        self.button_container: Optional[ClippingScrollList] = None
        self.improvement_list_scroll: Optional[ClippingScrollList] = None
        self.gold_label: Optional[ImageLabel] = None
        self.production_label: Optional[ImageLabel] = None
        self.food_label: Optional[ImageLabel] = None
        self.science_label: Optional[ImageLabel] = None
        self.culture_label: Optional[ImageLabel] = None
        self.border_label: Optional[ImageLabel] = None

        self.buildable_buttons: Dict[str, Button] = {}
        self.buildable_improvements: Dict[str, BaseCityImprovement] = {}
        self.buildable_units: Dict[str, CivilianBaseClass | MilitaryBaseClass] = {}

        self.should_log: bool = Debug.system_input()

        with self.canvas.before:
            self._bg_color_instr = Color(*self.bg_rgba)  # type: ignore
            self._bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect, bg_rgba=self._on_bg_rgba)  # type: ignore

        self.register()

    def _update_bg_rect(self, *_):
        self._bg_rect.size = self.size
        self._bg_rect.pos = self.pos

    def _on_bg_rgba(self, *_):
        self._bg_color_instr.rgba = self.bg_rgba  # type: ignore

    def register(self):
        self.accept("game.gameplay.city.starts_building_improvement", self.on_city_start_building_improvement)
        self.accept("game.gameplay.city.starts_building_unit", self.on_city_start_building_improvement)
        self.accept("game.gameplay.city.finish_building_improvement", self.on_city_finish_building_improvement)
        self.accept("game.gameplay.city.canceled_production", self.on_cancel_current_build)

    def get_screen(self) -> "GameUIScreen":
        screen = self.ref_screen()
        if screen is None:
            raise RuntimeError("CityUI screen reference is None.")
        return screen

    def set_city(self, city: City):
        self.city = city
        Clock.schedule_once(lambda *_: self.rebuild(city), 0)  # schedule on next frame # type: ignore

    def rebuild(self, city: City):
        self.clear_widgets()

        self.city_label = Label(text=str(city.name), size_hint=(1, None), height=50, bold=True, font_size=24)
        self.add_widget(self.city_label)

        stats = GridLayout(orientation="lr-tb", size_hint=(1, None), height=100, spacing=0, rows=2, cols=2)
        self.population_label = Label(text="Pop: ?", size_hint=(1, None), height=30, font_size=12)
        self.tiles_label = Label(text="Tiles: ?", size_hint=(1, None), height=30, font_size=12)
        self.player_label = Label(text="Owner: ?", size_hint=(1, None), height=30, font_size=12)
        self.is_capital_label = Label(text="Capital: ?", size_hint=(1, None), height=30, font_size=12)

        stats.add_widget(self.population_label)
        stats.add_widget(self.tiles_label)
        stats.add_widget(self.player_label)
        stats.add_widget(self.is_capital_label)
        self.add_widget(stats)

        current_layout = BoxLayout(orientation="horizontal", size_hint=(1, None), height=40, spacing=5)
        current_label = Label(
            text=str(t_("ui.player_ui.city.current_button_label")), size_hint=(0.3, None), height=30, font_size=16
        )
        self.current_button = Button(text="?", size_hint=(0.65, None), height=30)
        self.current_button.bind(on_press=self.on_cancel_current_build_btn_click)
        current_layout.add_widget(current_label)
        current_layout.add_widget(self.current_button)
        self.add_widget(current_layout)

        actions_label = Label(
            text=str(t_("ui.player_ui.city.actions_label")), size_hint=(1, None), height=30, font_size=16
        )
        self.add_widget(actions_label)

        self.button_container = ClippingScrollList(size_hint=(1, None), height=400)
        self.add_widget(self.button_container)

        improvements_lbl = Label(text="Improvements", size_hint=(1, None), height=30, font_size=16)
        self.add_widget(improvements_lbl)

        self.improvement_list_scroll = ClippingScrollList(size_hint=(1, None), height=dp(100), cols=3)
        self.add_widget(self.improvement_list_scroll)

        footer = GridLayout(orientation="lr-tb", size_hint=(1, None), height=80, spacing=10, cols=3, rows=2)
        self.gold_label = ImageLabel(
            text="Gold: ?",
            img_source="assets/icons/resources/core/basic/gold.png",
            size_hint=(1, None),
            height=30,
            font_size=12,
        )
        self.production_label = ImageLabel(
            text="Production: ?",
            img_source="assets/icons/resources/core/basic/production.png",
            size_hint=(1, None),
            height=30,
            font_size=12,
        )
        self.food_label = ImageLabel(
            text="Food: ?",
            img_source="assets/icons/resources/core/basic/food.png",
            size_hint=(1, None),
            height=30,
            font_size=12,
        )
        self.science_label = ImageLabel(
            text="Science: ?",
            img_source="assets/icons/resources/core/basic/science.png",
            size_hint=(1, None),
            height=30,
            font_size=12,
        )
        self.culture_label = ImageLabel(
            text="Culture: ?",
            img_source="assets/icons/resources/core/basic/culture.png",
            size_hint=(1, None),
            height=30,
            font_size=12,
        )
        self.border_label = ImageLabel(
            text="Border: ?", img_source="assets/icons/border_growth.png", size_hint=(1, None), height=30, font_size=12
        )
        footer.add_widget(self.gold_label)
        footer.add_widget(self.production_label)
        footer.add_widget(self.food_label)
        footer.add_widget(self.science_label)
        footer.add_widget(self.culture_label)
        footer.add_widget(self.border_label)
        self.add_widget(footer)

        food_collected = str(floor(city.food_collected.food.value))
        food_required = str(floor(city.new_population_food_required.food.value))
        self.population_label.text = str(
            t_(
                "ui.player_ui.city.population_label",
                {"population": city.population, "food_collected": food_collected, "food_required": food_required},
            )
        )
        self.is_capital_label.text = str(
            t_("ui.player_ui.city.is_capital_label", {"yes_no": "Yes" if city.is_capital else "No"})
        )
        self.tiles_label.text = str(t_("ui.player_ui.city.tiles_label", {"tiles": len(city.owned_tiles)}))
        if city.player is not None:
            self.player_label.text = str(
                t_("ui.player_ui.city.player_label", {"player": city.get_tile().get_owner().name})
            )

        ty: Yields = city.calculate_yield_from_tiles()
        self.gold_label.set_text(str(t_("ui.player_ui.city.gold_label", {"gold": ty.gold.value})))
        self.production_label.set_text(
            str(t_("ui.player_ui.city.production_label", {"production": ty.production.value}))
        )
        self.food_label.set_text(str(t_("ui.player_ui.city.food_label", {"food": ty.food.value})))
        self.science_label.set_text(str(t_("ui.player_ui.city.science_label", {"science": ty.science.value})))
        self.culture_label.set_text(str(t_("ui.player_ui.city.culture_label", {"culture": ty.culture.value})))
        self.border_label.set_text(
            str(
                t_(
                    "ui.player_ui.city.border_label",
                    {"current_points": city.border_growth_points, "required_points": city.border_growth_cost},
                )
            )
        )

        if city.is_building and city.building is not None:
            req_list = list(city.resource_required_amount.props(True).values())
            got_list = list(city.resource_collected.props(True).values())
            if len(req_list) == 0:
                self.logger.error("Resource required is None or empty.")
                raise AssertionError("Resource required is None or empty.")
            got = 0.0 if len(got_list) == 0 else got_list[0].value
            req = req_list[0].value
            building = city.get_building()
            self.current_button.text = str(
                t_(
                    "ui.player_ui.city.current_button_building",
                    {
                        "building": building.name if building is not None else "Unknown",
                        "resources_got": str(floor(got)),
                        "resources_required": str(floor(req)),
                    },
                )
            )
        elif not city.is_building:
            self.current_button.text = str(t_("ui.player_ui.city.current_button_idle"))

        self._fill_buildables(city)

        for imp in city._improvements:  # type: ignore
            self.improvement_list_scroll.add_widget(
                Label(text=str(imp.name), size_hint_y=None, height=30, font_size=12)
            )
        self.improvement_list_scroll._apply_clipping()  # type: ignore
        self.improvement_list_scroll.scroll_to_top()  # type: ignore

        # world visuals
        city.get_tile().get_renderer().update()

    def _fill_buildables(self, city: City) -> None:
        self.buildable_improvements.clear()
        self.buildable_units.clear()
        self.buildable_buttons.clear()
        assert self.button_container is not None
        self.button_container.clear_widgets()

        from gameplay.repositories.improvements import ImprovementsRepository

        def fmt(instance: BaseCityImprovement | CivilianBaseClass | MilitaryBaseClass) -> str:
            return f"{str(instance.name)} ({str(instance.resource_needed.name)}: {str(instance.amount_resource_needed.get_prop('production').value)})"

        # Improvements
        for class_name, class_ref in ImprovementsRepository.get_all_city_improvements().items():
            instance: BaseCityImprovement = class_ref(city.get_tile(), city.owner)  # type: ignore
            if not instance.conditions.are_met():  # type: ignore
                continue
            if type(instance) in city.get_improvements():  # type: ignore
                continue
            if any(i.__class__.__name__ == instance.__class__.__name__ for i in city.get_improvements()):
                continue

            btn = ButtonValue(text=fmt(instance), value=instance, size_hint=(1, None), height=50)
            btn.bind(on_press=lambda b: self.on_build_button_click(b))  # type: ignore
            self.buildable_improvements[class_name] = instance  # type: ignore
            self.buildable_buttons[class_name] = btn
            self.button_container.add_widget(btn)

        # Units
        for class_name, class_ref in UnitRepository.get_all_buildable_units().items():
            instance: CivilianBaseClass | MilitaryBaseClass = class_ref(city.get_tile(), city.owner)  # type: ignore
            if not instance.build_conditions.are_met():
                continue
            instance.is_being_build = True
            btn = ButtonValue(text=fmt(instance), value=instance, size_hint=(1, None), height=50)
            btn.bind(on_press=lambda b: self.on_unit_build_button_click(b))  # type: ignore
            self.buildable_units[class_name] = instance
            self.buildable_buttons[class_name] = btn
            self.button_container.add_widget(btn)

        self.button_container._apply_clipping()  # type: ignore
        self.button_container.scroll_to_top()

    def on_build_button_click(self, instance: ButtonValue):
        if self.city is None:
            return
        self.logger.debug(f"Requesting to build improvement: {instance.value} in city: {self.city.name}")
        MessengerGlobal.messenger.send(
            f"game.gameplay.city.request_start_building_improvement_{self.city.tag}", [self.city, instance.value]
        )

    def on_unit_build_button_click(self, instance: ButtonValue):
        if self.city is None:
            return
        self.logger.debug(f"Requesting to build unit: {instance.value} in city: {self.city.name}")
        MessengerGlobal.messenger.send(
            f"game.gameplay.city.request_start_building_unit_{self.city.tag}", [self.city, instance.value]
        )

    def on_city_start_building_improvement(self, city: City, improvement: BaseCityImprovement):
        if city == self.city:
            self.rebuild(city)

    def on_city_finish_building_improvement(self, city: City, improvement: BaseCityImprovement):
        if city == self.city:
            self.rebuild(city)

    def on_end_turn_process(self, turn: int):
        if self.city is not None:
            self.rebuild(self.city)

    def on_cancel_current_build(self, city: City):
        if city == self.city:
            self.rebuild(city)

    def on_cancel_current_build_btn_click(self, instance: Button):
        if self.city is None:
            raise AssertionError("City is None")
        self.logger.debug(f"Requesting to cancel current build in city: {self.city.name}")
        MessengerGlobal.messenger.send(
            f"game.gameplay.city.request_cancel_building_improvement_{self.city.tag}", [self.city]
        )

    def show(self, city: Optional[City] = None):
        self.logger.debug("Showing City UI")
        if city is not None:
            self.city = city
        if self.city is not None:
            self.rebuild(self.city)

        self.opacity = 1
        self.disabled = False
        self.hidden = False
        self.get_screen().register_non_collidable(self)

    def hide(self, auto_forget: bool = True):
        if self.hidden:
            if self.should_log:
                self.logger.debug("City UI is already hidden, skipping hide operation.")
            return
        self.logger.debug("Hiding City UI")
        if auto_forget:
            self.city = None
        self.opacity = 0
        self.disabled = True
        self.hidden = True
        self.get_screen().unregister_non_collidable(self)

    def is_hidden(self) -> bool:
        return self.hidden

from typing import Optional

from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from gameplay.city import City
from gameplay.tile_yield_modifier import TileYieldModifier
from menus.kivy.elements.clipping import ClippingScrollList
from menus.kivy.elements.image_label import ImageLabel
from menus.kivy.mixins.collidable import CollisionPreventionMixin


class CityUI(BoxLayout, CollisionPreventionMixin):
    def __init__(self, base, name, background_color=(0, 0, 0, 0), border=(0, 0, 0, 0), **kwargs):
        super().__init__(base=base, disable_zoom=True, orientation="vertical", **kwargs)  # type: ignore # The Layout class does not have a disable_zoom attribute but the CollisionPreventionMixin class does.
        self.pos_hint = {"x": 0, "center_y": 0.75}  # Align left & center vertically
        self.size_hint = (0.45, 0.2)  # type: ignore # Ensure fixed width and height
        self.background_color = (0, 0, 0, 1)  # Black background
        self.width = 400  # Explicitly set width
        self.height = 800  # Explicitly set height
        self.background_color = background_color
        self.border = border
        self.background_image = None
        self.base = base
        self.frame: Optional[BoxLayout] = None
        self.hidden: bool = False

        self.city_name = name
        self.city: Optional[City] = None
        self.city_label: Optional[Label] = None

        self.population_label: Optional[Label] = None
        self.is_capital_label: Optional[Label] = None
        self.tiles_label: Optional[Label] = None
        self.player_label: Optional[Label] = None

        self.current_layout: Optional[BoxLayout] = None
        self.current_label: Optional[Label] = None
        self.current_button: Optional[Button] = None

        self.actions_scroll: Optional[ScrollView] = None
        self.actions_label: Optional[Label] = None

        self.gold_label: Optional[ImageLabel] = None
        self.production_label: Optional[ImageLabel] = None
        self.food_label: Optional[ImageLabel] = None
        self.science_label: Optional[ImageLabel] = None
        self.culture_label: Optional[ImageLabel] = None

        self.add_widget(self.build())

    def set_city(self, city: City):
        self.city = city

    def update(self):
        if self.city is None:
            return
        self.city_name = self.city.name

        if self.city_label is not None:
            self.city_label.text = self.city_name

        if self.population_label is not None:
            self.population_label.text = f"Pop: {self.city.population}"

        if self.is_capital_label is not None:
            self.is_capital_label.text = f"Capital: {'Yes' if self.city.is_capital else 'No'}"

        if self.tiles_label is not None:
            self.tiles_label.text = f"Tiles: {len(self.city.owned_tiles)}"

        if self.player_label is not None and self.city.player is not None:
            self.player_label.text = f"Player: {str(self.city.player.name)}"

        if (
            self.gold_label is not None
            and self.production_label is not None
            and self.food_label is not None
            and self.science_label is not None
            and self.culture_label is not None
        ):
            tile_yield_modifier: TileYieldModifier = self.city.calculate_yield_from_tiles()
            tile_yield = tile_yield_modifier.calculate()

            self.gold_label.set_text(f"Gold: {tile_yield.gold.value}")
            self.production_label.set_text(f"Production: {tile_yield.production.value}")
            self.food_label.set_text(f"Food: {tile_yield.food.value}")
            self.science_label.set_text(f"Science: {tile_yield.science.value}")
            self.culture_label.set_text(f"Culture: {tile_yield.culture.value}")

    def build(self) -> BoxLayout:
        self.background_color = (0, 0, 0, 1)  # Black background

        # Main container (background black box)
        self.frame = BoxLayout(
            orientation="vertical",
            size_hint=(0.15, 0.55),
            width=400,
            height=800,
            padding=10,
            spacing=10,
            pos_hint={"right": 1, "center_y": 0.45},
        )

        with self.frame.canvas.before:  # type: ignore
            Color(0, 0, 0, 0.7)  # Black background with 70% opacity
            self.rect = Rectangle(size=self.frame.size, pos=self.frame.pos)

        def update_debug_rect(instance, value):
            self.rect.size = instance.size  # type: ignore
            self.rect.pos = instance.pos  # type: ignore

        self.frame.bind(size=update_debug_rect, pos=update_debug_rect)

        # City name label (Top)
        self.city_label = Label(text=self.city_name, size_hint=(1, None), height=50, bold=True, font_size=24)
        self.frame.add_widget(self.city_label)

        # City Stats Grid (Middle section)
        self.stats_grid = GridLayout(orientation="lr-tb", size_hint=(1, None), height=100, spacing=0, rows=2, cols=2)

        # Row 1
        self.population_label = Label(text="Pop: ?", size_hint=(1, None), height=30, font_size=12)
        self.tiles_label = Label(text="Tiles: ?", size_hint=(1, None), height=30, font_size=12)

        # Row 2
        self.player_label = Label(text="Owner: ?", size_hint=(1, None), height=30, font_size=12)
        self.is_capital_label = Label(text="Capital: ?", size_hint=(1, None), height=30, font_size=12)

        self.stats_grid.add_widget(self.population_label)
        self.stats_grid.add_widget(self.tiles_label)
        self.stats_grid.add_widget(self.player_label)
        self.stats_grid.add_widget(self.is_capital_label)

        self.frame.add_widget(self.stats_grid)

        self.current_layout = BoxLayout(orientation="horizontal", size_hint=(1, None), height=40, spacing=5)
        self.current_label = Label(text="Current", size_hint=(0.3, None), height=30, font_size=16)
        self.current_button = Button(text="Idle", size_hint=(0.65, None), height=30)
        self.current_layout.add_widget(self.current_label)
        self.current_layout.add_widget(self.current_button)

        self.frame.add_widget(self.current_layout)

        self.actions_label = Label(text="Actions", size_hint=(1, None), height=30, font_size=16)
        self.frame.add_widget(self.actions_label)

        # ScrollView Clipping Container
        clipping_container = ClippingScrollList(size_hint=(1, None), height=400)

        # Add buttons (Actions List)
        for i in range(20):
            btn = Button(text=f"Action {i + 1}", size_hint=(1, None), height=50)
            clipping_container.add_widget(btn)

        # Add ScrollView inside the clipping container
        self.frame.add_widget(clipping_container)

        # Footer (Bottom section)
        self.footer = GridLayout(orientation="lr-tb", size_hint=(1, None), height=80, spacing=10, cols=3, rows=2)

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

        self.footer.add_widget(self.gold_label)
        self.footer.add_widget(self.production_label)
        self.footer.add_widget(self.food_label)
        self.footer.add_widget(self.science_label)
        self.footer.add_widget(self.culture_label)

        self.frame.add_widget(self.footer)

        return self.frame

    def show(self, city: Optional[City] = None, auto_update: bool = True):
        """Makes the City View visible."""
        if self.frame is None:
            raise AssertionError("City view has not been built yet.")

        if city is not None:
            self.set_city(city)

        if auto_update:
            self.update()

        self.frame.opacity = 1
        self.frame.disabled = False
        self.hidden = False

    def hide(self, auto_forget: bool = True):
        """Hides the City View."""
        if self.frame is None:
            raise AssertionError("City view has not been built yet.")

        if auto_forget:
            self.city = None

        self.frame.opacity = 0
        self.frame.disabled = True
        self.hidden = True

    def is_hidden(self) -> bool:
        """Returns True if the City View is hidden."""
        return self.hidden

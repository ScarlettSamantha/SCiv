from typing import TYPE_CHECKING, Any, Dict, List, Optional

from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label

from managers.i18n import T_TranslationOrStr, t_
from managers.player import PlayerManager

if TYPE_CHECKING:
    from game import OpenCiv
    from gameplay.tile import Tile
    from gameplay.city import City
    from gameplay.unit import Unit


class DebugPanel(FloatLayout):
    def __init__(self, base: "OpenCiv", offset: int = 10, **kwargs: Any):
        super().__init__(**kwargs)
        self.base = base
        self.offset = offset  # Fixed pixel offset from the top

        self.frame = None
        self.panel = None
        self.rect = None

    def get_frame(self) -> FloatLayout:
        if self.frame is None:
            self.frame = self.build_debug_frame()
        return self.frame

    def build_debug_frame(self) -> FloatLayout:
        # --- Debug Panel (Top-Left Corner) ---
        self.frame = FloatLayout(
            size_hint=(None, None),
            width=300,
            height=700,
            pos_hint={"left": 1, "top": 0.975},
        )

        # Background rectangle (canvas.before)
        with self.frame.canvas.before:  # type: ignore
            Color(0, 0, 0, 0.7)  # Black background with 70% opacity
            self.rect = Rectangle(size=self.frame.size, pos=self.frame.pos)  # type: ignore

        def update_debug_rect(instance: Widget, value: Any):
            self.rect.size = instance.size  # type: ignore
            self.rect.pos = instance.pos  # type: ignore

        self.frame.bind(size=update_debug_rect, pos=update_debug_rect)  # type: ignore

        # Debug panel label
        self.panel = Label(
            text="Debug Info: None Yet",
            size_hint=(None, None),
            width=300,
            height=700,
            font_size="11sp",
            valign="top",
            halign="left",
            text_size=(300, 700),
            pos_hint={"left": 1, "top": 1},
            color=(1, 1, 1, 1),
            padding=10,
        )

        self.frame.add_widget(self.panel)
        return self.frame

    def update_debug_info_for_unit(self, unit: Optional["Unit"] = None) -> None:
        if self.panel is None or not self.frame:
            return

        if unit is None:
            self.panel.text = "Debug Info: None Yet"
            return

        data = self.unit_to_gui(unit)
        debug_text = "\n".join(f"{k}: {v}" for k, v in data.items())
        self.panel.text = f"Debug Info:\n{debug_text}"

    def update_debug_info_for_tile(self, tile: Optional["Tile"] = None) -> None:
        if self.panel is None or not self.frame:
            return

        if tile is None:
            self.panel.text = "Debug Info: None Yet"
            return

        data = self.tile_to_gui(tile)
        debug_text = "\n".join(f"{k}: {v}" for k, v in data.items())
        self.panel.text = f"Debug Info:\n{debug_text}"

    def tile_to_gui(self, tile: "Tile") -> Dict[str, Any]:
        terrain_name: T_TranslationOrStr = t_("civilization.nature.name")

        _improvements: List[str] = []
        if tile.city is not None:
            _improvements += [str(improvement.name) for improvement in tile.city.get_improvements()]

        for improvement in tile.get_improvements().all():
            _improvements.append(str(improvement.name))

        _units: List[str] = []
        for unit in tile.units.all():  # type: ignore
            data = self.unit_to_gui(unit)
            _units.append(f"{data['tag']} {data['name']}")

        yields = tile.get_tile_yield()

        data: Dict[str, Any] = {
            "tag": tile.tag,
            "x(col), y(row)": f"{tile.x}, {tile.y}",
            "terrain": terrain_name,
            "altitude": tile.altitude,
            "visible_sides": ",".join(map(str, tile.visible_sides.values())),
            "model": tile.model(),
            "passable": f"{str(tile.passable)}, {str(tile.passable_without_tech)}",
            "movement_cost": tile.movement_cost,
            "texture": tile.texture(),
            "class": tile.__class__.__name__,
            "owner": str(tile.owner.name) if tile.owner is not None else str(t_("civilization.nature.name")),
            "owner_city": str(tile.city_owner.name) if tile.city_owner else str(t_("civilization.nature.name")),
            "city": tile.city,
            "improvements": " | ".join(_improvements),
            "tile_yield": str(yields),
            "temperature": tile.temperature,
            "resources": tile.resources.flatten(),
            "features": tile.features,
            "units": ",".join(_units),
            "health": tile.health(),
            "damage": tile.damage,
            "pos": (tile.pos_x, tile.pos_y, tile.pos_z),
            "Hpr": ",".join(map(str, tile.hpr)),
            "effects": ",".join(tile.effects.get_effects().keys()),
            "resource_improved": "Yes" if tile.is_resource_improved() else "No",
            "Is selected": "Yes" if tile.is_selected else "No",
        }

        data["hex_data"] = {
            "altitude": tile.altitude,
            "biome": f"{tile.biome.id} - {tile.biome.name}",  # type: ignore
            "moisture": tile.moisture,
            r"is_[coast|sea|water|land|lake]": f"{tile.is_coast}|{tile.is_sea}|{tile.is_water}|{tile.is_land}|{tile.is_lake}",
            "is_city": tile.is_city(),
            "terrain": tile.terrain,
            "features": ",".join(str(feature) for feature in tile.features),
            "geoform": tile.geoforms,
            "zone": tile.zone,
            "hemisphere": tile.hemisphere,
            "resource['rating']": tile.resource["rating"] if tile.resource else None,
            "resource['type']": tile.resource["type"] if tile.resource else None,
        }

        if tile.units.has_any():
            if (unit := tile.units.first()) is not None:
                unit_stats = self.unit_to_gui(unit)
                data["hex_data"].setdefault("units", []).append(unit_stats)  # type: ignore

        if tile.city is not None:
            data["city"] = self.city_to_gui(tile, tile.city)
            data["city"] = "\n".join(f"{k}: {v}" for k, v in data["city"].items())

        data["hex_data"] = "\n".join(f"{k}: {v}" for k, v in data["hex_data"].items())

        return data

    def city_to_gui(self, tile: "Tile", city: "City") -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "name": city.name,
            "population": city.population,
            "is_capital": city.is_capital,
            "is_building": city.is_building,
            "building": city.building,
            "resources_needed": f"{city.resource_required_amount}/{city.resource_collected}",
            "owned_tiles": ",".join(str(tile.tag) for tile in city.owned_tiles),
        }
        return data

    def unit_to_gui(self, unit: "Unit") -> Dict[str, Any]:
        if unit.owner is None:
            owner_name = PlayerManager.get_nature()
        else:
            owner_name = str(unit.get_owner().civilization.name)

        model = None
        if unit.model is not None:
            model = unit.model
            model_pos = model.get_pos()
            model_pos_str = f"{round(model_pos[0], 4)}, {round(model_pos[1], 4)}, {round(model_pos[2], 4)}"
        else:
            model_pos_str = "None"

        return {
            "tag": unit.tag,
            "key": unit.key,
            "pos": f"{round(unit.pos_x, 4)}, {round(unit.pos_y, 4)}, {round(unit.pos_z, 4)}",
            "model_pos": model_pos_str,
            "name": str(unit.name),
            "description": unit.description,
            "owner": owner_name,
            "tile": unit.get_tile().tag if unit.tile is not None else "None",
            "health": f"{unit.health()}/{unit.max_health}",
            "damage": f"Mele: {unit.get_attack_power_mele()} | Ranged: {unit.get_attack_power_ranged()}",
            "defense": f"Mele: {unit.get_defense_mele()} | Ranged: {unit.get_defense_ranged()}",
            "attack_points": f"{unit.attack_points_left}/{unit.attack_points}",
            "attack_points_cost": f"Mele: {unit.attack_points_cost_mele} | Ranged: {unit.attack_points_cost_ranged}",
            "attack_range": unit.attack_range,
            "movement": f"{unit.moves_left}/{unit.max_moves}",
            "can_move": unit.can_move,
            "can_attack": unit.can_attack,
            "can_heal": unit.can_heal,
            "can_pillage": unit.can_pillage,
            "can_build": unit.can_build,
        }

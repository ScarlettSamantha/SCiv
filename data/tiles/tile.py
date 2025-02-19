from panda3d.core import NodePath, LRGBColor
from typing import Any, Optional, List
from data.terrain._base_terrain import BaseTerrain
from gameplay.combat.damage import DamageMode
from gameplay.improvement import Improvement
from gameplay.units.baseunit import BaseUnit
from gameplay.weather import BaseWeather
from gameplay.improvements import Improvements
from gameplay.tile_yield_modifier import TileYieldModifier, TileYield
from gameplay.city import City
from world.features._base_feature import BaseFeature
from world.items._base_item import BaseItem
from managers.player import PlayerManager, Player


class Tile:
    def __init__(self, id: Any, x: int, y: int, node: NodePath):
        self.id = id
        self.x: int = x
        self.y: int = y
        self.node: NodePath = node
        self.tile_terrain: BaseTerrain

    def __repr__(self) -> str:
        return f"{str(self.id)}@{str(self.x)},{str(self.y)}"

    def set_color(self, color: tuple[float, float, float, float]):
        self.node.setColor(*color)

    def get_node(self) -> NodePath:
        return self.node

    def set_terrain(self, terrain: BaseTerrain):
        self.tile_terrain = terrain

    def get_terrain(self) -> Optional[BaseTerrain]:
        return self.tile_terrain

    def _reset_tile_properties_to_default(self):
        # Has this tile been destroyed.
        self.destroyed = False
        self.grid_position = None
        self.raw_position = None

        # This is the height of the tile in relation to the average sea level in meters.
        self.gameplay_height = 0

        # None is nature.
        self.player: Optional[Player] = None

        # Base health and if damagable declarations
        self.damagable = False
        self.health = 100
        self.damage = 0

        # Does it take damage over time ?
        self.damage_per_turn_mode = DamageMode.DAMAGE_NONE
        self.damage_per_turn = 0.0

        # Does it damage units over time ?
        self.damage_per_turn_on_units_mode = DamageMode.DAMAGE_NONE
        self.damage_per_turn_on_units = 0.0

        # Does it damamge improvements over time ?
        self.damage_per_turn_on_improvements_mode = DamageMode.DAMAGE_NONE
        self.damage_per_turn_on_improvements = 0.0

        # Can units walk over ?
        self.walkable = True
        # Can ships make it through ?
        self.sailable = False
        # Is this deep water ?
        self.deep = False
        # Can airplanes fly over ?
        self.flyable = True
        # Is space above accessable ?
        self.space_above = True
        # Can it be dug under ?
        self.diggable = True
        # Can it be build on ?
        self.buidable = True
        # If it can be walked over with clibing.
        self.climbable = True
        # If it can be claimed.
        self.claimable = True
        # If units can breeth
        self.air_breatheable = True
        # Can things grow on it ?
        self.growable = True

        # How difficult it is to move over this tile messured in movement cost (MC)
        self.movement_cost = 1.0

        # What weather is the tile having ?
        self.weather: BaseWeather | None = None

        # What features does this tile contain ?
        self.features: List[BaseFeature] = list()
        # Does this have any units ?
        self.units: List[BaseUnit] = list()
        # Does this have improvements ?
        self._improvements: Improvements = Improvements()
        # Does this have items sitting on top of it ?
        self.items: List[BaseItem] = list()
        # What kind of states apply to this object ?
        self.states: List[Any] = []

        # Does this contain an city ?
        self.city: City | None = None
        # Who if anybody is the owner of this tile ?
        self.owner: Player | None = None
        # Who has claimed the tile but does not own it ?
        self.claimants: List[Any] = []

        # We configure base tile yield mostly just for debugging.
        self.tile_yield: TileYieldModifier = TileYieldModifier(
            values=TileYield(
                gold=0.0,
                production=0.0,
                science=0.0,
                food=0.0,
                culture=0.0,
                housing=0.0,
            ),
            mode=TileYieldModifier.MODE_SET,
        )

        self.meshCollider = True

    def color(self) -> tuple[float, float, float] | LRGBColor:
        if self.tile_terrain is not None:
            return self.tile_terrain.color()
        try:
            return self.tile_terrain.fallback_color()  # type: ignore
        except AttributeError:
            return (1, 1, 1)

    def model(self):
        return self.tile_terrain.model()

    def texture(self):
        return self.tile_terrain.texture()

    def setTerrain(self, terrain: BaseTerrain) -> None:
        self.tile_terrain = terrain

    def addTileYield(self, tileYield: TileYield) -> None:
        self.tile_yield.values += tileYield  # type: ignore

    def tileYield(self) -> TileYieldModifier:
        return self.tile_yield

    def improvements(self) -> Improvements:
        return self._improvements

    def build(self, improvement: Improvement) -> None:
        self._improvements.add(improvement)

    def found(
        self,
        player: Optional[Player] = None,
        population: int = 1,
        capital: bool = False,
    ):
        if player is None:
            player = PlayerManager.player()
        self.city = City.found_new(
            name="Test city", tile=self, population=population, is_capital=capital
        )

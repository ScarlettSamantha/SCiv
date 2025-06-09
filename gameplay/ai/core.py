import weakref
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Dict, List, Tuple, Type

from gameplay._units import Units
from gameplay.ai.goal import Goal, Goals
from gameplay.ai.goals.eliminate_unit import EliminateUnit
from gameplay.ai.memory import Memories, Memory
from gameplay.ai.task import Task, Tasks
from gameplay.cities import Cities
from gameplay.personality import Personality
from gameplay.player_tiles import PlayerTiles
from gameplay.repositories.tile import TileRepository
from gameplay.tiles.base_tile import Tile
from gameplay.unit import Unit
from helpers.cache import Optional
from managers.game import World
from managers.player import PlayerManager

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.vision import Vision


class AI(ABC):
    UNIT_REAL_VISION_RADIUS: int = 3  # The real vision radius of a unit is how the engine actually sees the world

    def __init__(self, player: "Player"):
        self.player: "Player" = player
        self.logger = self.player.logger.getChild("ai")
        self.logger.debug(f"AI created for player {str(self.player.name)} with personality {self.player.personality}")

        self.control_units: weakref.ReferenceType[Units] = weakref.ref(self.player.units)
        self.control_cities: weakref.ReferenceType[Cities] = weakref.ref(self.player.cities)
        self.control_tiles: weakref.ReferenceType[PlayerTiles] = weakref.ref(self.player.tiles)
        self.vision: weakref.ReferenceType["Vision"] = weakref.ref(self.player.vision)

        self.end_goal: Goals = self.register_end_goal()
        self.goals: Goals = self.register_goals()

        self.memory: Memories = Memories()
        self.tasks: Tasks = Tasks()
        self.personality: Personality = self.player.personality

    def get_memories(self) -> Memories:
        return self.memory

    def get_tasks(self) -> Tasks:
        return self.tasks

    def get_units(self) -> Units:
        if self.control_units() is None:
            raise ValueError("Units reference is None")
        units = self.control_units()
        if units is None:
            raise ValueError("Units reference is None")
        return units

    def get_cities(self) -> Cities | None:
        return self.control_cities()

    def get_tiles(self) -> PlayerTiles | None:
        return self.control_tiles()

    def get_player(self) -> "Player":
        return self.player

    def get_end_goal(self) -> Goals:
        return self.end_goal

    def get_goals(self) -> Goals:
        return self.goals

    def get_personality(self) -> Personality:
        return self.personality

    def add_memory(self, memory: Memory) -> None:
        self.memory.add_memory(memory)

    def add_task(self, task: Task) -> None:
        self.tasks.add_task(task)

    def add_goal(self, goal: Goal) -> None:
        self.goals.add_goal(goal)

    def add_end_goal(self, goal: Goal) -> None:
        self.end_goal.add_goal(goal)

    def has_goal(self) -> bool:
        return len(self.goals) > 0

    def remove_end_goal(self, goal: Goal) -> None:
        self.end_goal.remove_goal(goal)

    def remove_goal(self, goal: Goal) -> None:
        self.goals.remove_goal(goal)

    def remove_memory(self, memory: Memory) -> None:
        self.memory.remove_memory(memory)

    def remove_task(self, task: Task) -> None:
        self.tasks.remove_task(task)

    @abstractmethod
    def register_end_goal(self) -> Goals: ...

    @abstractmethod
    def register_goals(self) -> Goals: ...

    @abstractmethod
    def on_turn_end(self) -> None: ...

    @abstractmethod
    def on_turn_start(self) -> None: ...

    @abstractmethod
    def on_game_start(self) -> None: ...

    def spawn_unit(self, unit: Type["Unit"], tile: Tile) -> "Unit":
        """
        Spawn a unit on the given tile.
        """
        return unit.spawn_on(tile, self.get_player())

    def get_world_state(self) -> Dict[Tuple[int, int], Tile]:
        """
        Get the world state.
        """
        return self.world()

    def world(self) -> Dict[Tuple[int, int], Tile]:
        return World.get_singleton_instance().get_grid()

    def get_tile_count(self) -> int:
        return len(self.world())

    def get_players(self) -> Dict[int, "Player"]:
        """
        Get all players in the game.
        """
        return PlayerManager.all()

    def get_targets(self) -> Dict[Tuple[int, int], Tile]:
        targets: Dict[Tuple[int, int], Tile] = {}
        for unit in self.get_units().all():
            targets.update(self.get_target_for_unit(unit))
        return targets

    def create_goals_for_unit(self, executing_unit: Unit) -> Optional[Goal]:
        targets = self.get_target_for_unit(executing_unit)
        if len(targets) == 0:
            return None

        for tile in targets.values():
            if tile.units.has_any():
                target_unit: Unit | None = tile.units.first()
                if target_unit is None or target_unit.owner == self.get_player():
                    continue
                return EliminateUnit(target=target_unit, executing_unit=executing_unit, parent=weakref.ref(self))

    def get_goals_for_unit(self, executing_unit: Unit) -> List[Goal]:
        """
        Get the goals for a specific unit.
        """
        goals: List[Goal] = []
        for unit_goal in self.get_goals():
            if unit_goal.for_unit and unit_goal.get_executing_unit() == executing_unit:
                goals.append(unit_goal)
        return goals

    def get_target_for_unit(self, unit: Unit) -> Dict[Tuple[int, int], Tile]:
        targets: Dict[Tuple[int, int], Tile] = {}
        for tile in unit.look(self.UNIT_REAL_VISION_RADIUS):
            if tile.is_city() and tile.owner != self.get_player():
                targets[tile.x, tile.y] = tile
            elif tile.units.has_any() and self.is_target(tile.units.all()[0]):
                targets[tile.x, tile.y] = tile
            elif tile.improvements().has_any() and tile.owner != self.get_player():
                targets[tile.x, tile.y] = tile
        return targets

    def get_threats(self) -> Dict[Tuple[int, int], Tile]:
        threats: Dict[Tuple[int, int], Tile] = {}
        for unit in self.get_units().all():
            threats.update(self.get_threat_for_unit(unit))
        return threats

    def get_threat_for_unit(self, unit: Unit) -> Dict[Tuple[int, int], Tile]:
        threats: Dict[Tuple[int, int], Tile] = {}
        for tile in unit.look(self.UNIT_REAL_VISION_RADIUS):
            if tile.is_city() and tile.owner != self.get_player():
                threats[tile.x, tile.y] = tile
            elif tile.units.has_any() and self.is_threat(tile.units.all()[0]):
                threats[tile.x, tile.y] = tile
        return threats

    def is_target(self, unit: Unit) -> bool:
        """
        Check if the unit is a target.
        """
        result = unit.owner != self.get_player()
        return result

    def is_threat(self, unit: Unit) -> bool:
        """
        Check if the unit is a threat.
        """
        result = unit.owner != self.get_player()
        return result

    def check_route_to(self, _from: "Tile", to: "Tile", radius: int = 5) -> bool:
        return TileRepository.astar(_from, to, radius) is not None

    def move_unit(self, unit: Unit, to: Tile, on_tile_visit: Optional[Callable[["Tile"], None]] = None) -> None:
        """
        Move a unit to a specific tile.
        """
        movement_points = unit.moves_left
        if (path := TileRepository.astar(unit.get_tile(), to, movement_points)) is not None:
            for path_tile in path:
                unit.move(path_tile)
                if on_tile_visit is not None:
                    on_tile_visit(path_tile)

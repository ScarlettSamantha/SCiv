import random
import weakref
from abc import ABC, abstractmethod
from logging import Logger
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Tuple, Type, cast

from gameplay._units import Units
from gameplay.ai.goal import Goal, Goals
from gameplay.ai.memory import Memories, Memory
from gameplay.ai.task import Task, Tasks
from gameplay.cities import Cities
from gameplay.personality import Personality
from gameplay.player_tiles import PlayerTiles
from gameplay.repositories.tile import TileRepository
from helpers.cache import Optional
from managers.entity import EntityType
from managers.game import EntityManager, World
from managers.player import PlayerManager
from managers.turn import Turn

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.tile import Tile
    from gameplay.unit import Unit
    from gameplay.vision import Vision


class AI(ABC):
    UNIT_REAL_VISION_RADIUS: int = 3  # The real vision radius of a unit is how the engine actually sees the world

    def __init__(self, player: "Player"):
        self._player: weakref.ReferenceType["Player"] = weakref.ref(player)
        self.turn_action_register: Dict[int, List[Callable[..., None]]] = {}
        self.logger: Logger = self.player.logger.getChild(suffix="ai")
        self.logger.debug(f"AI created for player {str(self.player.name)} with personality {self.player.personality}")

        self.control_units: weakref.ReferenceType["Units"] = weakref.ref(self.player.units)
        self.control_cities: weakref.ReferenceType["Cities"] = weakref.ref(self.player.cities)
        self.control_tiles: weakref.ReferenceType[PlayerTiles] = weakref.ref(self.player.tiles)
        self.vision: weakref.ReferenceType["Vision"] = weakref.ref(self.player.vision)
        self.unit_directions: Dict[int, Tuple[int, int]] = {}

        self.end_goal: Goals = self.register_end_goal()
        self.goals: Goals = self.register_goals()

        self.memory: Memories = Memories()
        self.tasks: Tasks = Tasks()
        self.personality: Personality = self.player.personality

    def __getstate__(self) -> Dict[str, Any]:
        data: Dict[str, Any] = self.__dict__.copy()

        player: "Player | None" = self._player()
        if player is None:
            raise ValueError("Player reference is None, cannot serialize AI state.")

        data.pop("control_units", None)
        data.pop("control_cities", None)
        data.pop("control_tiles", None)
        data.pop("logger", None)
        data.pop("vision", None)
        data.pop("personality", None)
        data.pop("turn_action_register", None)
        data.pop("rules", None)
        data["player"] = player.get_tag()
        data["cls_ref"] = f"{self.__class__.__module__}.{self.__class__.__name__}"
        del data["_player"]
        return data

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.__dict__.update(state)
        player_ref: "Player | None" = self._player()
        if player_ref is not None:
            self.logger = player_ref.logger.getChild("ai")

    def dump(self) -> Dict[str, Any]:
        return {
            "player": self.player.get_tag(),
            "cls_ref": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "end_goal": self.end_goal.dump(),
            "goals": self.goals.dump(),
            "memory": self.memory.dump(),
            "tasks": self.tasks.dump(),
        }

    def load_from_state(self, state: Dict[str, Any]) -> None:
        self._player = cast(
            weakref.ReferenceType["Player"],
            EntityManager.get_singleton_instance().get_ref_weak(EntityType.PLAYER, state.get("player", "")),
        )
        self.logger = self.player.logger.getChild("ai")
        self.logger.debug("Loading AI state")
        self.control_cities = weakref.ref(self.player.cities)
        self.control_units = weakref.ref(self.player.units)
        self.control_tiles = weakref.ref(self.player.tiles)
        self.vision = weakref.ref(self.player.vision)
        self.end_goal = Goals()
        self.end_goal.load_state(state.get("end_goal", {}))
        self.goals = Goals()
        self.goals.load_state(state.get("goals", {}))
        self.memory = Memories()
        self.memory.load_state(state.get("memory", {}))
        self.tasks = Tasks()
        self.tasks.load_state(state.get("tasks", {}))
        self.personality = self.player.personality

    @property
    def player(self) -> "Player":
        player: "Player | None" = self._player()
        if player is None:
            self._player = weakref.ref(PlayerManager.get_nature())
            assert self._player() is not None, "Player reference is None"
            return self._player()  # type: ignore
        return player

    def get_memories(self) -> Memories:
        return self.memory

    def get_tasks(self) -> Tasks:
        return self.tasks

    def get_units(self) -> Units:
        if self.control_units() is None:
            self.control_units = weakref.ref(self.player.units)
        units: "Units | None" = self.control_units()
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
        self.memory.add_memory(memory=memory)

    def add_task(self, task: Task) -> None:
        self.tasks.add_task(task=task)

    def add_goal(self, goal: Goal) -> None:
        self.goals.add_goal(goal=goal)

    def add_end_goal(self, goal: Goal) -> None:
        self.end_goal.add_goal(goal=goal)

    def has_goal(self) -> bool:
        return len(self.goals) > 0

    def remove_end_goal(self, goal: Goal) -> None:
        self.end_goal.remove_goal(goal=goal)

    def remove_goal(self, goal: Goal) -> None:
        self.goals.remove_goal(goal=goal)

    def remove_memory(self, memory: Memory) -> None:
        self.memory.remove_memory(memory=memory)

    def remove_task(self, task: Task) -> None:
        self.tasks.remove_task(task=task)

    @abstractmethod
    def register_end_goal(self) -> Goals: ...

    @abstractmethod
    def register_goals(self) -> Goals: ...

    def execute_turn_action(self, turn: int) -> None:
        if turn in self.turn_action_register.keys():
            for action in self.turn_action_register[turn]:
                action()
            del self.turn_action_register[turn]

    def on_turn_end(self) -> None:
        turn: int = Turn.get_singleton_instance().get_turn()
        self.execute_turn_action(turn=turn)

    @abstractmethod
    def on_turn_start(self) -> None: ...

    @abstractmethod
    def on_game_start(self) -> None: ...

    def spawn_unit(self, unit: Type["Unit"], tile: "Tile") -> "Unit":
        return unit.spawn_on(tile=tile, player=self.get_player())

    def get_world_state(self) -> Dict[Tuple[int, int], "Tile"]:
        return self.world()

    def world(self) -> Dict[Tuple[int, int], "Tile"]:
        return World.get_singleton_instance().get_grid()

    def get_tile_count(self) -> int:
        return len(self.world())

    def get_players(self) -> Dict[int, "Player"]:
        return PlayerManager.all()

    def get_targets(self) -> Dict[Tuple[int, int], "Tile"]:
        targets: Dict[Tuple[int, int], "Tile"] = {}
        for unit in self.get_units().all():
            targets.update(self.get_target_for_unit(unit))
        return targets

    def create_goals_for_unit(self, executing_unit: "Unit") -> Optional[Goal]:
        from gameplay.ai.goals.eliminate_unit import EliminateUnit

        targets: Dict[Tuple[int, int], "Tile"] = self.get_target_for_unit(executing_unit)
        if len(targets) == 0:
            return None

        for tile in targets.values():
            if tile.units.has_any():
                target_unit: "Unit | None" = tile.units.first()
                if target_unit is None or target_unit.owner == self.get_player():
                    continue
                return EliminateUnit(target=target_unit, executing_unit=executing_unit, parent=weakref.ref(self))

    def get_goals_for_unit(self, executing_unit: "Unit") -> List[Goal]:
        goals: List[Goal] = []
        for unit_goal in self.get_goals():
            if unit_goal.for_unit and unit_goal.get_executing_unit() == executing_unit:
                goals.append(unit_goal)
        return goals

    def get_target_for_unit(self, unit: "Unit") -> Dict[Tuple[int, int], "Tile"]:
        targets: Dict[Tuple[int, int], "Tile"] = {}
        for tile in unit.look(radius=self.UNIT_REAL_VISION_RADIUS):
            if tile.is_city() and tile.owner != self.get_player():
                targets[tile.x, tile.y] = tile
            elif tile.units.has_any() and self.is_target(tile.units.first()):  # type: ignore
                targets[tile.x, tile.y] = tile
            elif tile.improvements().has_any() and tile.owner != self.get_player():
                targets[tile.x, tile.y] = tile
        return targets

    def get_threats(self) -> Dict[Tuple[int, int], "Tile"]:
        threats: Dict[Tuple[int, int], Tile] = {}
        for unit in self.get_units().all():
            threats.update(self.get_threat_for_unit(unit))
        return threats

    def get_threat_for_unit(self, unit: "Unit") -> Dict[Tuple[int, int], "Tile"]:
        threats: Dict[Tuple[int, int], "Tile"] = {}
        for tile in unit.look(self.UNIT_REAL_VISION_RADIUS):
            if tile.is_city() and tile.owner != self.get_player():
                threats[tile.x, tile.y] = tile
            elif tile.units.has_any() and self.is_threat(tile.units.first()):  # type: ignore
                threats[tile.x, tile.y] = tile
        return threats

    def is_target(self, unit: "Unit") -> bool:
        result = unit.owner != self.get_player()
        return result

    def is_threat(self, unit: "Unit") -> bool:
        result = unit.owner != self.get_player()
        return result

    def check_route_to(self, _from: "Tile", to: "Tile", radius: int = 5) -> bool:
        return TileRepository.astar(start=_from, goal=to, movement_points=radius) is not None

    def move_unit(self, unit: "Unit", to: "Tile", on_tile_visit: Optional[Callable[["Tile"], None]] = None) -> None:
        movement_points: int | float = unit.moves_left
        if (path := TileRepository.astar(start=unit.get_tile(), goal=to, movement_points=movement_points)) is not None:
            for path_tile in path:
                unit.move(tile=path_tile)
                if on_tile_visit is not None:
                    on_tile_visit(path_tile)

    def _select_wander_tile(self, unit: "Unit") -> Optional["Tile"]:
        current: "Tile" = unit.get_tile()
        neighbors: List["Tile"] = [
            t
            for t in TileRepository.get_neighbors(current, 1, True, False)
            if t.is_passable() and not t.units.has_any() and not t.is_lake and not t.is_water
        ]
        if not neighbors:
            return None

        uid: int = id(unit)
        prev_dir: Tuple[int, int] | None = self.unit_directions.get(uid, None)

        if prev_dir:
            scored: List[Tuple[int, "Tile"]] = []
            for t in neighbors:
                score: int = (t.x - current.x) * prev_dir[0] + (t.y - current.y) * prev_dir[1]
                scored.append((score, t))

            best_score, best_tile = max(scored, key=lambda pair: pair[0])
            if best_score > 0:
                return best_tile

        return random.choice(neighbors)

    def on_wander(self, unit: "Unit") -> None:
        while unit.moves_left > 0:
            current: Tile = unit.get_tile()
            next_tile: Tile | None = self._select_wander_tile(unit)
            if not next_tile:
                break

            self.unit_directions[id(unit)] = ((next_tile.x - current.x), (next_tile.y - current.y))
            self.move_unit(unit=unit, to=next_tile)

            new_goal: Goal | None = self.create_goals_for_unit(executing_unit=unit)
            if new_goal:
                self.add_goal(goal=new_goal)
                return

    def on_fixed_turn(self, turn: int, callable: Callable[[], None]) -> None:
        if turn in self.turn_action_register:
            raise ValueError(f"Turn {turn} already has an action registered.")
        self.turn_action_register.setdefault(turn, []).append(callable)

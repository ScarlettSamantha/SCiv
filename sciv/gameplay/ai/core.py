import datetime
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
from gameplay.personalities.base import BasePersonality
from gameplay.player_tiles import PlayerTiles
from gameplay.repositories.tile import TileRepository
from helpers.cache import Optional
from managers.entity import EntityType
from managers.player import PlayerManager
from managers.turn import Turn

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.tile import Tile
    from gameplay.unit import Unit
    from gameplay.vision import Vision


class AI(ABC):
    UNIT_REAL_VISION_RADIUS: int = 3

    def __init__(self, player: "Player"):
        self._player: weakref.ReferenceType["Player"] = weakref.ref(player)
        self.turn_action_register: Dict[int, List[Callable[..., None]]] = {}
        self.logger: Logger = self.player.logger.getChild(suffix="ai")
        self.logger.debug(f"AI created for player {str(self.player.name)} with personality {self.player.personality}")
        self.control_units: weakref.ReferenceType["Units"] = weakref.ref(self.player.units)
        self.control_cities: weakref.ReferenceType["Cities"] = weakref.ref(self.player.cities)
        self.control_tiles: weakref.ReferenceType[PlayerTiles] = weakref.ref(self.player.tiles)
        self.vision: weakref.ReferenceType["Vision"] = weakref.ref(self.player.vision)
        self.unit_directions: Dict[int, Tuple[float, float]] = {}
        self.unit_recent: Dict[int, List[Tuple[int, int]]] = {}
        self.end_goal: Goals = self.register_end_goal()
        self.goals: Goals = self.register_goals()
        self.memory: Memories = Memories()
        self.tasks: Tasks = Tasks()
        self.personality: BasePersonality = self.player.personality

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

    def load_state(self, state: Dict[str, Any]) -> None:
        from managers.game import EntityManager

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
        self.end_goal.load_state(state.get("end_goal", {}), self)
        self.goals = Goals()
        self.goals.load_state(state.get("goals", {}), self)
        self.memory = Memories()
        self.memory.load_state(state.get("memory", {}))
        self.tasks = Tasks()
        self.tasks.load_state(state.get("tasks", {}))
        self.personality = self.player.personality
        self.turn_action_register = state.get("turn_action_register", {})
        self.unit_directions = state.get("unit_directions", {})
        self.unit_recent = state.get("unit_recent", {})

    def get_logger(self) -> Logger:
        return self.logger

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

    def get_personality(self) -> BasePersonality:
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
        from managers.game import World

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

    def _recent_for(self, uid: int) -> List[Tuple[int, int]]:
        if uid not in self.unit_recent:
            self.unit_recent[uid] = []
        return self.unit_recent[uid]

    def _push_recent(self, uid: int, coord: Tuple[int, int], cap: int = 16) -> None:
        max_recent_positions: int = cap
        recent_positions = self._recent_for(uid)
        recent_positions.append(coord)
        if len(recent_positions) > max_recent_positions:
            del recent_positions[0]

    def _move_adjacent(self, unit: "Unit", to: "Tile") -> bool:
        neighbor_radius: int = 1
        use_same_ring: bool = True
        include_diagonals: bool = False
        current: "Tile" = unit.get_tile()
        if to in TileRepository.get_neighbors(current, neighbor_radius, use_same_ring, include_diagonals):
            unit.move(tile=to)
            return True
        return False

    def _select_wander_tile(self, unit: "Unit") -> Optional["Tile"]:
        neighbor_radius: int = 1
        use_same_ring: bool = True
        include_diagonals: bool = False
        random_explore_probability: float = 0.12
        revisit_tile_weight_multiplier: float = 0.3
        base_weight: float = 1.0
        alignment_weight: float = 1.0
        outward_weight: float = 0.7
        noise_amplitude: float = 0.5
        minimum_weight: float = 1e-6

        current: "Tile" = unit.get_tile()
        neighbors: List["Tile"] = [
            t
            for t in TileRepository.get_neighbors(current, neighbor_radius, use_same_ring, include_diagonals)
            if t.is_passable() and not t.units.has_any() and not t.is_lake and not t.is_water
        ]
        if not neighbors:
            return None

        uid: int = id(unit)
        last_direction: Tuple[float, float] | None = self.unit_directions.get(uid, None)
        recent_positions: List[Tuple[int, int]] = self._recent_for(uid)

        if recent_positions:
            centroid_x = sum(x for x, _ in recent_positions) / float(len(recent_positions))
            centroid_y = sum(y for _, y in recent_positions) / float(len(recent_positions))
        else:
            centroid_x = float(current.x)
            centroid_y = float(current.y)

        if random.random() < random_explore_probability:
            candidate_pool = [t for t in neighbors if (t.x, t.y) not in recent_positions] or neighbors
            return random.choice(candidate_pool)

        weights: List[float] = []
        distance_from_centroid_current = (current.x - centroid_x) * (current.x - centroid_x) + (
            current.y - centroid_y
        ) * (current.y - centroid_y)

        for t in neighbors:
            step_dx = t.x - current.x
            step_dy = t.y - current.y

            alignment = step_dx * (last_direction[0] if last_direction else 0.0) + step_dy * (
                last_direction[1] if last_direction else 0.0
            )
            distance_to_centroid_neighbor = (t.x - centroid_x) * (t.x - centroid_x) + (t.y - centroid_y) * (
                t.y - centroid_y
            )
            outward_delta = max(0.0, distance_to_centroid_neighbor - distance_from_centroid_current)

            revisit_multiplier = revisit_tile_weight_multiplier if (t.x, t.y) in recent_positions else 1.0

            weight = base_weight
            weight += alignment_weight * max(0.0, alignment)
            weight += outward_weight * outward_delta
            weight += random.random() * noise_amplitude
            weight *= revisit_multiplier
            if weight <= 0.0:
                weight = minimum_weight

            weights.append(weight)

        return random.choices(neighbors, weights=weights, k=1)[0]

    def on_wander(self, unit: "Unit") -> None:
        time_budget_ms: int = 250
        max_steps: int = 16
        direction_smooth_prev: float = 0.7
        direction_smooth_new: float = 0.3
        repetition_check_min_len: int = 8
        uniqueness_threshold_ratio: float = 0.5

        loop_started_at: datetime.datetime = datetime.datetime.now()
        time_budget: datetime.timedelta = datetime.timedelta(milliseconds=time_budget_ms)
        steps_taken: int = 0
        uid: int = id(unit)

        while (
            unit.moves_left > 0
            and steps_taken < max_steps
            and (datetime.datetime.now() - loop_started_at) < time_budget
        ):
            current_tile: Tile = unit.get_tile()
            next_tile: Tile | None = self._select_wander_tile(unit)
            if not next_tile:
                break

            step_dx = next_tile.x - current_tile.x
            step_dy = next_tile.y - current_tile.y

            prev_dir: Tuple[float, float] | None = self.unit_directions.get(uid, None)
            if prev_dir is None:
                updated_direction = (float(step_dx), float(step_dy))
            else:
                updated_direction = (
                    prev_dir[0] * direction_smooth_prev + step_dx * direction_smooth_new,
                    prev_dir[1] * direction_smooth_prev + step_dy * direction_smooth_new,
                )

            self.unit_directions[uid] = updated_direction
            self._push_recent(uid, (current_tile.x, current_tile.y))

            if not self._move_adjacent(unit, next_tile):
                self.move_unit(unit=unit, to=next_tile)

            steps_taken += 1

            recent_positions = self._recent_for(uid)
            if len(recent_positions) >= repetition_check_min_len:
                unique_count = len(set(recent_positions))
                threshold = int(len(recent_positions) * uniqueness_threshold_ratio)
                if unique_count <= threshold:
                    self.unit_directions[uid] = (0.0, 0.0)
                    break

        new_goal: Goal | None = self.create_goals_for_unit(executing_unit=unit)
        if new_goal:
            self.add_goal(goal=new_goal)
            return

    def on_fixed_turn(self, turn: int, callable: Callable[[], None]) -> None:
        if turn in self.turn_action_register:
            raise ValueError(f"Turn {turn} already has an action registered.")
        self.turn_action_register.setdefault(turn, []).append(callable)

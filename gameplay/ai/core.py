import weakref
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Tuple, Type

from gameplay._units import Units
from gameplay.ai.goal import Goal, Goals
from gameplay.ai.memory import Memories, Memory
from gameplay.ai.task import Task, Tasks
from gameplay.cities import Cities
from gameplay.personality import Personality
from gameplay.player_tiles import PlayerTiles
from gameplay.tiles.base_tile import BaseTile
from gameplay.units.unit_base import UnitBaseClass
from managers.game import World

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.vision import Vision


class AI(ABC):
    def __init__(self, player: "Player"):
        self.player: "Player" = player

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

    def get_units(self) -> Units | None:
        return self.control_units()

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

    def _add_memory(self, memory: Memory) -> None:
        self.memory.add_memory(memory)

    def _add_task(self, task: Task) -> None:
        self.tasks.add_task(task)

    def _add_goal(self, goal: Goal) -> None:
        self.goals.add_goal(goal)

    def _add_end_goal(self, goal: Goal) -> None:
        self.end_goal.add_goal(goal)

    def _remove_end_goal(self, goal: Goal) -> None:
        self.end_goal.remove_goal(goal)

    def _remove_goal(self, goal: Goal) -> None:
        self.goals.remove_goal(goal)

    def _remove_memory(self, memory: Memory) -> None:
        self.memory.remove_memory(memory)

    def _remove_task(self, task: Task) -> None:
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

    def spawn_unit(self, unit: Type["UnitBaseClass"], tile: BaseTile) -> "UnitBaseClass":
        """
        Spawn a unit on the given tile.
        """
        return unit.spawn_on(tile, self.get_player())

    def world(self) -> Dict[Tuple[int, int], BaseTile]:
        return World.get_singleton_instance().get_grid()

    def get_tile_count(self) -> int:
        return len(self.world())

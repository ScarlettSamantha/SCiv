import weakref
from abc import ABC, abstractmethod

from gameplay._units import Units
from gameplay.ai.goal import Goal, Goals
from gameplay.ai.memory import Memories, Memory
from gameplay.ai.task import Task, Tasks
from gameplay.cities import Cities
from gameplay.personality import Personality
from gameplay.player import Player
from gameplay.player_tiles import PlayerTiles


class AI(ABC):
    def __init__(self, player: Player):
        self.player: Player = player

        self.units: weakref.ReferenceType[Units] = weakref.ref(self.player.units)
        self.cities: weakref.ReferenceType[Cities] = weakref.ref(self.player.cities)
        self.tiles: weakref.ReferenceType[PlayerTiles] = weakref.ref(self.player.tiles)

        self.end_goal: Goals = self.register_end_goal()
        self.goals: Goals = self.register_goals()

        self.memory: Memories = Memories()
        self.tasks: Tasks = Tasks()
        self.personality: Personality = self.player.personality

    def _get_memories(self) -> Memories:
        return self.memory

    def _get_tasks(self) -> Tasks:
        return self.tasks

    def _get_units(self) -> Units | None:
        return self.units()

    def _get_cities(self) -> Cities | None:
        return self.cities()

    def _get_tiles(self) -> PlayerTiles | None:
        return self.tiles()

    def _get_player(self) -> Player:
        return self.player

    def _get_end_goal(self) -> Goals:
        return self.end_goal

    def _get_goals(self) -> Goals:
        return self.goals

    def _get_personality(self) -> Personality:
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

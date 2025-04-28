from typing import Iterator


class Goal:
    name: str
    description: str

    def __init__(self):
        self.achieved: bool = False

    def is_achieved(self) -> bool:
        """Check if the goal is achieved."""
        return self.achieved

    def mark_achieved(self) -> None:
        """Mark the goal as achieved."""
        self.achieved = True

    def not_achieved(self) -> None:
        """Mark the goal as not achieved."""
        self.achieved = False


class Goals:
    def __init__(self):
        self.goals: list[Goal] = []

    def add_goal(self, goal: Goal) -> None:
        self.goals.append(goal)

    def remove_goal(self, goal: Goal) -> None:
        self.goals.remove(goal)

    def get_goals(self) -> list[Goal]:
        return self.goals

    def __iter__(self) -> Iterator[Goal]:
        return iter(self.goals)

    def __len__(self) -> int:
        return len(self.goals)

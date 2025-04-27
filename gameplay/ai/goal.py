class Goal:
    pass


class Goals:
    def __init__(self):
        self.goals: list[Goal] = []

    def add_goal(self, goal: Goal) -> None:
        self.goals.append(goal)

    def remove_goal(self, goal: Goal) -> None:
        self.goals.remove(goal)

    def get_goals(self) -> list[Goal]:
        return self.goals

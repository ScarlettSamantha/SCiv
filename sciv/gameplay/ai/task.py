from typing import Any, Dict, List


class Task:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.completed = False

    def complete(self):
        self.completed = True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "completed": str(self.completed),
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        self.name = state.get("name", "")
        self.description = state.get("description", "")
        self.completed = state.get("completed", "False").lower() == "true"


class Tasks:
    def __init__(self):
        self.tasks: List[Task] = []

    def add_task(self, task: Task):
        self.tasks.append(task)

    def remove_task(self, task: Task):
        if task in self.tasks:
            self.tasks.remove(task)

    def dump(self) -> List[Dict[str, Any]]:
        return [task.dump() for task in self.tasks]

    def load_state(self, state: List[Dict[str, Any]]):
        self.tasks = []
        for task_state in state:
            task: Task = Task.__new__(Task)
            task.load_state(task_state)
            self.tasks.append(task)

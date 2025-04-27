from typing import List


class Task: ...


class Tasks:
    def __init__(self):
        self.tasks: List[Task] = []

    def add_task(self, task: Task):
        self.tasks.append(task)

    def remove_task(self, task: Task):
        if task in self.tasks:
            self.tasks.remove(task)

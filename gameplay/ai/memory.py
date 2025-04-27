from typing import List


class Memory: ...


class Memories:
    def __init__(self):
        self.memories: List[Memory] = []

    def add_memory(self, memory: Memory):
        self.memories.append(memory)

    def get_memories(self) -> List[Memory]:
        return self.memories

    def clear_memories(self):
        self.memories = []

    def remove_memory(self, memory: Memory):
        if memory in self.memories:
            self.memories.remove(memory)

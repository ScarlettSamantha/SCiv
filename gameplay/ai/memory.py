from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Iterator, List

from managers.i18n import T_TranslationOrStr


class Memory(ABC):
    name: T_TranslationOrStr
    description: T_TranslationOrStr

    def __init__(self, associated_value: Any, associated_value_type: str, auto_acquire: bool = True):
        self.associated_value = associated_value
        self.associated_value_type = associated_value_type

        self.acquired_at: datetime = datetime.now()
        self.lost_at: datetime | None = None
        self.is_lost: bool = False

        if auto_acquire:
            self.acquire()

    def __str__(self):
        return f"{self.name} - {self.description}[{self.associated_value}@{self.associated_value_type}]"

    def loose(self):
        """Mark the memory as lost."""
        self.lost_at = datetime.now()
        self.is_lost = True
        self._on_lost()

    def acquire(self):
        """Mark the memory as acquired."""
        self.acquired_at = datetime.now()
        self.is_lost = False
        self._on_acquired()

    def is_acquired(self) -> bool:
        """Check if the memory is acquired."""
        return not self.is_lost

    def get_associated_value(self) -> Any:
        """Get the associated value of the memory."""
        return self.associated_value

    def get_associated_value_type(self) -> str:
        """Get the type of the associated value."""
        return self.associated_value_type

    def get_acquired_at(self) -> datetime:
        """Get the time when the memory was acquired."""
        return self.acquired_at

    def get_lost_at(self) -> datetime | None:
        """Get the time when the memory was lost."""
        return self.lost_at

    def get_name(self) -> T_TranslationOrStr:
        """Get the name of the memory."""
        return self.name

    def get_description(self) -> T_TranslationOrStr:
        """Get the description of the memory."""
        return self.description

    @abstractmethod
    def _on_acquired(self):
        """Called when the memory is acquired."""
        pass

    @abstractmethod
    def _on_lost(self):
        """Called when the memory is lost."""
        pass

    @abstractmethod
    def on_remember(self):
        """Called when the memory is remembered."""
        pass


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

    def __iter__(self) -> Iterator[Memory]:
        return iter(self.memories)

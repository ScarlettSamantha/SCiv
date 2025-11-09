from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Iterator, List

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
        self.lost_at = datetime.now()
        self.is_lost = True
        self._on_lost()

    def acquire(self):
        self.acquired_at = datetime.now()
        self.is_lost = False
        self._on_acquired()

    def is_acquired(self) -> bool:
        return not self.is_lost

    def get_associated_value(self) -> Any:
        return self.associated_value

    def get_associated_value_type(self) -> str:
        return self.associated_value_type

    def get_acquired_at(self) -> datetime:
        return self.acquired_at

    def get_lost_at(self) -> datetime | None:
        return self.lost_at

    def get_name(self) -> T_TranslationOrStr:
        return self.name

    def get_description(self) -> T_TranslationOrStr:
        return self.description

    @abstractmethod
    def _on_acquired(self):
        pass

    @abstractmethod
    def _on_lost(self):
        pass

    @abstractmethod
    def on_remember(self):
        pass

    def dump(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "associated_value": self.associated_value,
            "associated_value_type": self.associated_value_type,
            "acquired_at": self.acquired_at.isoformat(),
            "lost_at": self.lost_at.isoformat() if self.lost_at else None,
            "is_lost": self.is_lost,
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        self.name = state.get("name", "")
        self.description = state.get("description", "")
        self.associated_value = state.get("associated_value")
        self.associated_value_type = state.get("associated_value_type", "")
        self.acquired_at = datetime.fromisoformat(state.get("acquired_at", ""))
        lost_at_value = state.get("lost_at")
        self.lost_at = datetime.fromisoformat(lost_at_value) if lost_at_value is not None else None
        self.is_lost = state.get("is_lost", False)


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

    def dump(self) -> List[Dict[str, Any]]:
        return [memory.dump() for memory in self.memories]

    def load_state(self, state: List[Dict[str, Any]]):
        self.memories = []
        for memory_state in state:
            memory: Memory = Memory.__new__(Memory)
            memory.load_state(memory_state)
            self.memories.append(memory)

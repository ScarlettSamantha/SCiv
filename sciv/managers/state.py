from typing import Any, Dict

flag_types = str | int | bool | float


class State:
    _flags: Dict[str, flag_types] = {}  # Should be used for simpler flags that are going to be changed often.
    _state: Dict[
        str, Any
    ] = {}  # Cant do lambda's because when pickled it will transform into a string its a known thing.

    @classmethod
    def set_state(cls, key: str, value: Any) -> None:
        cls._state[key] = value

    @classmethod
    def get_state(cls, key: str) -> Any:
        return cls._state.get(key, None)

    @classmethod
    def remove_state(cls, key: str) -> None:
        cls._state.pop(key, None)

    @classmethod
    def clear_state(cls) -> None:
        cls._state.clear()

    @classmethod
    def get_states(cls) -> Dict[str, Any]:
        return cls._state

    @classmethod
    def has_state(cls, key: str) -> bool:
        return key in cls._state

    @classmethod
    def load_state(cls, state: Dict[str, Any]) -> None:
        cls._state = state

    @classmethod
    def set_flag(cls, key: str, value: flag_types) -> None:
        cls._flags[key] = value

    @classmethod
    def get_flag(cls, key: str) -> flag_types | None:
        return cls._flags.get(key, None)

    @classmethod
    def remove_flag(cls, key: str) -> None:
        cls._flags.pop(key, None)

    @classmethod
    def clear_flags(cls) -> None:
        cls._flags.clear()

    @classmethod
    def get_flags(cls) -> Dict[str, flag_types]:
        return cls._flags

    @classmethod
    def has_flag(cls, key: str) -> bool:
        return key in cls._flags

    @classmethod
    def load_flags(cls, flags: Dict[str, flag_types]) -> None:
        cls._flags = flags

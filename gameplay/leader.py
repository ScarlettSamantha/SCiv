from typing import List, Optional

from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone
from system.effects import Effect


class Leader:
    def __init__(
        self,
        key: Optional[str],
        name: T_TranslationOrStrOrNone,
        description: T_TranslationOrStrOrNone,
        icon: Optional[str] = None,
    ) -> None:
        self.key: str = key if key is not None else ""
        self.name: T_TranslationOrStr = name if name is not None else ""
        self.icon: str | None = icon if icon is not None else None
        self.description: T_TranslationOrStr = description if description is not None else ""

        self._effects: List[Effect] = []

    @property
    def effects(self) -> List[Effect]:
        return self._effects

    @effects.setter
    def effects(self, effects: List[Effect]) -> None:
        self._effects = effects

    def add_effect(self, effect: Effect) -> None:
        self._effects.append(effect)

    def get_effects(self) -> List[Effect]:
        return self._effects

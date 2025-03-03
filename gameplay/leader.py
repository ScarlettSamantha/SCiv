from __future__ import annotations
from typing import Optional

from gameplay.effect import Effects, Effect
from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone
from system.saving import SaveAble


class Leader(SaveAble):
    def __init__(
        self,
        key: Optional[str],
        name: T_TranslationOrStrOrNone,
        description: T_TranslationOrStrOrNone,
        icon: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.key: str = key if key is not None else ""
        self.name: T_TranslationOrStr = name if name is not None else ""
        self.icon: str | None = icon if icon is not None else None
        self.description: T_TranslationOrStr = description if description is not None else ""

        self._effects: Effects = Effects()

    @property
    def effects(self) -> Effects:
        return self._effects

    @effects.setter
    def effects(self, effects: Effects) -> None:
        self._effects = effects

    def add_effect(self, effect: Effect) -> None:
        self._effects.add(effect=effect)

    def get_effects(self) -> Effects:
        return self._effects

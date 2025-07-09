from typing import Optional

from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone


class Leader:
    def __init__(
        self,
        key: Optional[str],
        name: T_TranslationOrStrOrNone,
        description: T_TranslationOrStrOrNone,
        icon: Optional[str] = None,
    ) -> None:
        from system.effects import Effects

        self.key: str = key if key is not None else ""
        self.name: T_TranslationOrStr = name if name is not None else ""
        self.icon: str | None = icon if icon is not None else None
        self.description: T_TranslationOrStr = description if description is not None else ""

        self._effects: Effects = Effects(self)

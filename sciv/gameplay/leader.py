from typing import Any, Dict, Optional

from managers.i18n import T_TranslationOrStr, T_TranslationOrStrOrNone, Translation, get_i18n


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

    def dump(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name.get_key() if isinstance(self.name, Translation) else "",
            "description": self.description.get_key() if isinstance(self.description, Translation) else "",
            "icon": self.icon,
            "cls_ref": f"{self.__class__.__module__}.{self.__class__.__name__}",
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        self.key = state.get("key", "")
        self.name = get_i18n().from_key(state.get("name", ""))
        self.description = state.get("description", "")
        self.icon = state.get("icon", None)

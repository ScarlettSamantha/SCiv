from typing import Any

from managers.i18n import T_TranslationOrStr


class Plane:
    def __init__(
        self,
        key: str,
        name: T_TranslationOrStr,
        description: T_TranslationOrStr,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.key: str = key
        self.name: T_TranslationOrStr = name
        self.description: T_TranslationOrStr = description

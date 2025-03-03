from __future__ import annotations

from managers.i18n import T_TranslationOrStr
from system.saving import SaveAble
from typing import Any


class Plane(SaveAble):
    def __init__(
        self,
        key: str,
        name: T_TranslationOrStr,
        description: T_TranslationOrStr,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        SaveAble.__init__(self, *args, **kwargs)
        self.key: str = key
        self.name: T_TranslationOrStr = name
        self.description: T_TranslationOrStr = description

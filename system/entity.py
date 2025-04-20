from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from direct.showbase.DirectObject import DirectObject

from helpers.cache import Cache
from helpers.colors import Colors, Tuple4f
from helpers.placeholder import Placeholder
from managers.i18n import T_TranslationOrStrOrNone

if TYPE_CHECKING:
    from main import SCIV


class BaseEntity(ABC, DirectObject):
    name: T_TranslationOrStrOrNone = None
    description: T_TranslationOrStrOrNone = None

    icon: str | Path | None = Placeholder.getPlaceholderImagePathSmallIcon()
    icon_border_color: Tuple4f = Colors.YELLOW

    def __init__(self):
        super().__init__()
        self.entity_key: Optional[str] = None
        self.entity_type_ref: Optional[str] = None
        self.is_registered: bool = False

        if Cache.has_instance() is False:
            raise AssertionError("Cache instance is not set.")

        self.base: "SCIV" = Cache.get_showbase_instance()

    def __getstate__(self) -> Dict[str, Any]:
        state = self.__dict__.copy()
        if "base" in state:
            del state["base"]
        return state

    def get_registered_status(self) -> bool:
        return self.is_registered

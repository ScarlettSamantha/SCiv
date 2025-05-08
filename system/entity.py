from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Union
from weakref import ReferenceType

from direct.showbase.DirectObject import DirectObject


from helpers.cache import Cache
from helpers.colors import Colors, Tuple4f
from helpers.placeholder import Placeholder
from managers.i18n import T_TranslationOrStrOrNone

if TYPE_CHECKING:
    from main import SCIV
    from gameplay.tiles.base_tile import BaseTile


class BaseEntity(ABC, DirectObject):
    name: T_TranslationOrStrOrNone = None
    description: T_TranslationOrStrOrNone = None

    icon: str | Path | None = Placeholder.getPlaceholderImagePathSmallIcon()
    icon_border_color: Tuple4f = Colors.YELLOW

    def __init__(self, tile: Optional[Union["BaseTile", ReferenceType["BaseTile"]]] = None, *args: Any, **kwargs: Any):
        super().__init__()
        self.entity_key: Optional[str] = None
        self.entity_type_ref: Optional[str] = None
        self.is_registered: bool = False
        self.tile: Optional[Union["BaseTile", ReferenceType["BaseTile"]]] = tile

        if Cache.has_instance() is False:
            raise AssertionError("Cache instance is not set.")

        self.base: "SCIV" = Cache.get_showbase_instance()

    def get_tile(self) -> "BaseTile":
        if self.tile is None:
            raise ValueError("Tile is None")

        # Delay import so you don’t hit TYPE_CHECKING guard at module load
        from gameplay.tiles.base_tile import BaseTile

        # If it’s already a BaseTile instance, return it directly
        if isinstance(self.tile, BaseTile):
            return self.tile

        # If it’s a weakref to a BaseTile, dereference and return
        # Dereference self.tile directly as it's expected to be a ReferenceType
        tile_obj = self.tile()
        if not isinstance(tile_obj, BaseTile):
            raise TypeError(f"Reference resolved to unexpected type {type(tile_obj)}")
        return tile_obj

    def set_tile(self, tile: "BaseTile") -> None:
        self.tile = tile

    def __getstate__(self) -> Dict[str, Any]:
        state = self.__dict__.copy()
        if "base" in state:
            del state["base"]
        return state

    def get_registered_status(self) -> bool:
        return self.is_registered

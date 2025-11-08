from io import BytesIO
from pathlib import Path
from typing import Any, Tuple

from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from system.asset_archive import P3DAssetArchive  # type: ignore


def image_widget_from_vfs(virtual_path: str, **kwargs: Any) -> Image:
    from helpers.cache import Cache

    vfs: P3DAssetArchive = Cache.get_asset_archive()
    data: bytes = vfs.read_bytes(virtual_path)

    return image_widget_from_encoded(data, ext=Path(virtual_path).suffix.lstrip("."), **kwargs)


def image_widget_from_encoded(data: bytes, ext: str, **kwargs: Any) -> Image:
    try:
        ci = CoreImage(BytesIO(data), ext=ext.lstrip(".").lower())
    except Exception as e:
        raise RuntimeError(f"Failed to load image from encoded data with extension '{ext}': {e}") from e
    return Image(texture=ci.texture, **kwargs)


def image_widget_from_raw(
    rgba: bytes,
    size: Tuple[int, int],
    colorfmt: str = "rgba",
    bufferfmt: str = "ubyte",
    **kwargs: Any,
) -> Image:
    tex = Texture.create(size=size, colorfmt=colorfmt)
    tex.blit_buffer(rgba, colorfmt=colorfmt, bufferfmt=bufferfmt)
    return Image(texture=tex, **kwargs)

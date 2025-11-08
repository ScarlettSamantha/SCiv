import os
from io import BytesIO
from logging import Logger
from os import path
from os.path import exists
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple
from zlib import crc32

from direct.gui.OnscreenImage import OnscreenImage
from gameplay.resources.core.basic.culture import Culture
from gameplay.resources.core.basic.faith import Faith
from gameplay.resources.core.basic.food import Food
from gameplay.resources.core.basic.gold import Gold
from gameplay.resources.core.basic.production import Production
from gameplay.resources.core.basic.science import Science
from helpers.images import draw_text_on_image
from helpers.os import WindowsHelper
from kivy.core.image import Image as CoreImage
from kivy.resources import resource_find  # type: ignore
from kivy.uix.image import Image as KivyImage
from mixins.singleton import Singleton
from panda3d.core import NodePath, TextFont, Texture
from PIL import Image, ImageFont
from PIL import Image as PILImage
from PIL import ImageFont as PILImageFont
from system.asset_archive import P3DAssetArchive

if TYPE_CHECKING:
    from sciv.game import OpenCiv


class AssetManager(Singleton):
    texture_cache: Dict[str, Texture] = {}
    font_cache: Dict[str, TextFont] = {}
    model_cache: Dict[str, NodePath] = {}
    kivy_image_cache: Dict[str, CoreImage] = {}
    pil_image_cache: Dict[str, PILImage.Image] = {}
    pil_font_cache: Dict[Tuple[str, str], PILImageFont.FreeTypeFont] = {}

    base: Optional["OpenCiv"] = None
    _logger: Optional[Logger] = None

    def __setup__(self):
        if self._logger is None and self.base is not None:
            self._logger = self.base.logger.engine.getChild("manager.asset")

    @classmethod
    def reset(cls) -> None:
        """Reset the asset manager caches."""
        cls.texture_cache.clear()
        cls.font_cache.clear()
        cls.model_cache.clear()
        cls.kivy_image_cache.clear()
        cls.pil_image_cache.clear()
        cls.pil_font_cache.clear()

    @classmethod
    def logger(cls) -> Logger:
        if cls._logger is None and cls.base is not None:
            cls._logger = cls.base.logger.engine.getChild("manager.asset")

        if cls._logger is None:  # mostly a sanity check and to stop pyright/ruff from complaining.
            raise AssertionError("Logger not set for AssetManager, even after attempting to set it.")

        return cls._logger

    @classmethod
    def load_texture(cls, path: str, use_cache: bool = True) -> Texture:
        cache_key: str = cls._calculate_cache_key(path)
        if use_cache and cache_key in cls.texture_cache:
            return cls.texture_cache[cache_key]

        cls.logger().debug(f"Loading texture {path}")

        if cls.base is None:  # only have to check this here as cache does not need base.
            raise ValueError("Base not set for AssetManager")

        if WindowsHelper.is_windows():
            path = WindowsHelper.win32_to_unix_path(path)

        texture: Texture = cls.base.loader.load_texture(path)

        if use_cache:
            cls.texture_cache[cache_key] = texture

        return texture

    @classmethod
    def load_font(cls, path: str, use_cache: bool = True) -> TextFont:
        cache_key: str = cls._calculate_cache_key(path)
        if use_cache and cache_key in cls.font_cache.keys():
            return cls.font_cache[cache_key]

        cls.logger().debug(f"Loading font {path}")

        if cls.base is None:  # only have to check this here as cache does not need base.
            raise ValueError("Base not set for AssetManager")

        if WindowsHelper.is_windows():
            path = WindowsHelper.win32_to_unix_path(path)

        font: TextFont = cls.base.loader.load_font(path)

        if use_cache:
            cls.font_cache[cache_key] = font

        return font

    @classmethod
    def load_model(cls, path: str, use_cache: bool = True) -> NodePath:
        from helpers.debug import Debug

        cache_key: str = cls._calculate_cache_key(path)

        if use_cache and cache_key in cls.model_cache:
            # Return a deep copy of the cached model to ensure independent modification
            return cls.model_cache[cache_key].copyTo(NodePath())  # type: ignore

        if Debug.system_loading_models():
            cls.logger().debug(f"Loading model {path}")

        if cls.base is None:
            raise ValueError("Base not set for AssetManager")

        if WindowsHelper.is_windows():
            path = WindowsHelper.win32_to_unix_path(path)

        model: NodePath | None = cls.base.loader.load_model(path)

        if model is None:
            raise ValueError(f"Failed to load model from {path}")

        if use_cache:
            # Cache the original model
            cls.model_cache[cache_key] = model

        # Return the original model since it's not coming from the cache
        return model

    @classmethod
    def load_image(cls, path: str, resize: Optional[Tuple[int, int]] = None, use_cache: bool = True) -> OnscreenImage:
        cache_key: str = cls._calculate_cache_key(path)

        if use_cache and cache_key in cls.texture_cache:
            texture: Texture = cls.texture_cache[cache_key]
        else:
            cls.logger().debug(f"Loading image {path}")
            if cls.base is None:
                raise ValueError("Base not set for AssetManager")

            if WindowsHelper.is_windows():
                path = WindowsHelper.win32_to_unix_path(path)

            texture: Texture = cls.base.loader.load_texture(path)

            if use_cache:
                cls.texture_cache[cache_key] = texture

        # Create a new OnscreenImage instance with the cached texture
        image = OnscreenImage(image=texture)  # type: ignore

        if resize:
            image.setScale(  # type: ignore
                resize[0] / image.getTexture().getOrigFileXSize(),  # type: ignore
                1,
                resize[1] / image.getTexture().getOrigFileYSize(),  # type: ignore
            )

        return image

    @classmethod
    def load_kivy_image(
        cls, path: str, size_hint_y: Optional[int] = None, height: Optional[int] = None, use_cache: bool = True
    ) -> KivyImage:
        resolved_path: str = resource_find(path)  # type: ignore
        if not resolved_path or not isinstance(resolved_path, str):  # type: ignore
            raise FileNotFoundError(f"Could not resolve path for Kivy image: {path}")

        cache_key: str = cls._calculate_cache_key(resolved_path)

        if use_cache and cache_key in cls.kivy_image_cache:
            core_image = cls.kivy_image_cache[cache_key]
        else:
            if not exists(resolved_path):
                raise FileNotFoundError(f"File does not exist: {resolved_path}")
            core_image = CoreImage(resolved_path)
            if use_cache:
                cls.kivy_image_cache[cache_key] = core_image

        img_widget = KivyImage(texture=core_image.texture, size_hint_y=size_hint_y)  # type: ignore

        if height is not None:
            img_widget.height = height

        return img_widget

    @classmethod
    def set_base(cls, base: "OpenCiv") -> None:
        cls.base = base

    @classmethod
    def _calculate_cache_key(cls, path: str) -> str:
        return str(crc32(path.encode()))

    @classmethod
    def load_pil_image(cls, path: str, use_cache: bool = True) -> PILImage.Image:
        """Load a PIL image directly from assets."""
        if use_cache and path in cls.pil_image_cache:
            pil_image = cls.pil_image_cache.get(path, None)
            if pil_image is None:
                raise FileNotFoundError(f"PIL image not found in cache: {path}")
            return pil_image

        if not exists(path):
            raise FileNotFoundError(f"PIL image not found: {path}")

        cls.logger().debug(f"Loading PIL image {path}")
        image = PILImage.open(path).convert("RGBA")
        if use_cache:
            cls.pil_image_cache[path] = image

        return image

    @classmethod
    def load_pil_font(cls, path: str, size: int = 24, use_cache: bool = True) -> PILImageFont.FreeTypeFont:
        """Load a PIL font (truetype) directly from assets."""
        key: Tuple[str, str] = (path, str(size))
        if use_cache and key in cls.pil_font_cache:
            pil_font = cls.pil_font_cache.get(key, None)
            if pil_font is None:
                raise FileNotFoundError(f"PIL font not found in cache: {path}")
            return pil_font

        if not exists(path):
            raise FileNotFoundError(f"PIL font not found: {path}")

        cls.logger().debug(f"Loading PIL font {path} with size {size}")
        font = PILImageFont.truetype(path, size)
        if use_cache:
            cls.pil_font_cache[key] = font
        return font

    @classmethod
    def generate_static_assets(cls, tile_set: str = "default"):
        from helpers.cache import Cache
        from helpers.images import create_stacked_horizontal_images
        from helpers.paths import PathsHelper

        assets: P3DAssetArchive = Cache.get_asset_archive()

        def _read_bytes(vp: str) -> bytes:
            return assets.read_bytes(vp)

        def _first_existing_icon(icon_rel: str) -> Optional[str]:
            cand: List[str] = []
            ic = icon_rel.lstrip("/")
            if ic.startswith("assets/"):
                cand.append(ic)
            cand.extend(
                [
                    f"assets/icons/{tile_set}/{ic}",
                    f"assets/icons/{tile_set}/resources/{ic}",
                    f"assets/icons/default/{ic}",
                    f"assets/icons/default/resources/{ic}",
                    f"assets/{ic}" if not ic.startswith("assets/") else ic,
                ]
            )
            seen: Set[str] = set()
            for c in cand:
                if c in seen:
                    continue
                seen.add(c)
                try:
                    _read_bytes(c)
                    return c
                except Exception:
                    continue
            return None

        def generate_static_resource_icons():
            out_dir = f"{PathsHelper.get_data_dir()}/assets/generated/icons/resources/core/basic"
            if not path.exists(out_dir):
                os.makedirs(out_dir, exist_ok=True)

            basic_resources = (Gold, Production, Food, Faith, Science, Culture)
            for R in basic_resources:
                r = R()
                icon_vp = _first_existing_icon(r.icon)
                if not icon_vp:
                    continue

                base_img = Image.open(BytesIO(_read_bytes(icon_vp))).convert("RGBA")
                for i in range(1, 6):
                    stacked = create_stacked_horizontal_images([base_img] * i, offset=(17, 0))
                    stacked.save(f"{out_dir}/{str(r.name).lower()}_{i}.png")

                font_bytes = _read_bytes("assets/fonts/Washington.ttf")
                for i in range(6, 50):
                    img_width, img_height = base_img.size
                    font = ImageFont.truetype(BytesIO(font_bytes), 46)
                    bbox = font.getbbox(str(i))
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    pos_x = (img_width - text_width) / 4
                    pos_y = (img_height - text_height) / 4
                    draw_text_on_image(
                        base_img.copy(),
                        [(str(i), (int(pos_x), int(pos_y)))],
                        font,
                        font_size=46,
                        save=True,
                        save_path=f"{out_dir}/{str(r.name).lower()}_{i}.png",
                        outline=True,
                        outline_color=(0, 0, 0, 255),
                        outline_width=1,
                    )

            def generate_static_population_icons():
                from helpers.paths import PathsHelper

                out_tpl = (
                    PathsHelper.get_data_dir() + "/assets/generated/icons/resources/core/basic/populationx128_{num}.png"
                )
                base_icon_vp = f"assets/icons/{tile_set}/resources/core/basic/populationx128.png"
                if not _first_existing_icon("resources/core/basic/populationx128.png"):
                    base_icon_vp = "assets/icons/default/resources/core/basic/populationx128.png"

                font_bytes = _read_bytes("assets/fonts/Washington.ttf")
                font = ImageFont.truetype(BytesIO(font_bytes), 46)

                for i in range(1, 50):
                    img = Image.open(BytesIO(_read_bytes(base_icon_vp))).convert("RGBA")
                    img_w, img_h = img.size
                    text = str(i)
                    bbox = font.getbbox(text)
                    text_w = bbox[2] - bbox[0]
                    text_h = bbox[3] - bbox[1]
                    pos_x = (img_w - text_w) / 2
                    pos_y = ((img_h - text_h) / 2) + 32
                    draw_text_on_image(
                        base_image=img,
                        text_entries=[(text, (pos_x, pos_y))],
                        font_path=font,
                        font_size=46,
                        text_color=(0, 0, 0, 1),
                        save=True,
                        save_path=out_tpl.format(num=i),
                        outline=True,
                        outline_color=(0, 0, 0, 255),
                        outline_width=1,
                    )

            generate_static_resource_icons()
            generate_static_population_icons()

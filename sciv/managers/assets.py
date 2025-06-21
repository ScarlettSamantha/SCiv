from logging import Logger
from os.path import exists
from typing import TYPE_CHECKING, Dict, Optional, Tuple
from zlib import crc32

from direct.gui.OnscreenImage import OnscreenImage
from kivy.core.image import Image as CoreImage
from kivy.resources import resource_find  # type: ignore
from kivy.uix.image import Image as KivyImage
from panda3d.core import NodePath, TextFont, Texture
from PIL import Image, ImageFont
from PIL import Image as PILImage
from PIL import ImageFont as PILImageFont

from gameplay.resources.core.basic.culture import Culture
from gameplay.resources.core.basic.faith import Faith
from gameplay.resources.core.basic.food import Food
from gameplay.resources.core.basic.gold import Gold
from gameplay.resources.core.basic.production import Production
from gameplay.resources.core.basic.science import Science
from helpers.debug import Debug
from helpers.images import draw_text_on_image
from mixins.singleton import Singleton
from helpers.windows import WindowsHelper

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
        if WindowsHelper.is_windows():
            path = WindowsHelper.win32_to_unix_path(path)

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
        def generate_static_resource_icons():
            from helpers.images import create_stacked_horizontal_images

            basic_resources = Gold, Production, Food, Faith, Science, Culture
            for resource in basic_resources:
                resource_instance = resource()
                base_path = (
                    f"assets/icons/{tile_set}/"
                    if resource_instance.icon.startswith("resources")
                    else f"assets/icons/{tile_set}/resources/"
                )
                icon_path = f"{base_path}/{resource_instance.icon}"
                if not icon_path:
                    continue

                image = Image.open(icon_path).convert("RGBA")
                font_size = 32
                text_vertical_offset = 0
                text_horizontal_offset = 0

                directory = "assets/generated/icons/resources/core/basic"
                if not exists(directory):
                    from os import makedirs

                    makedirs(directory)

                # Create a stacked horizontal image with the icon
                for i in range(1, 6):
                    stacked_image = create_stacked_horizontal_images([image] * i, offset=(17, 0))
                    stacked_image.save(f"{directory}/{str(resource_instance.name).lower()}_{i}.png")

                for i in range(6, 50):
                    img_width, img_height = image.size

                    font = ImageFont.truetype("assets/fonts/Washington.ttf", font_size)

                    bbox = font.getbbox(str(i))
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]

                    pos_x = (img_width - text_width) / 4 + text_horizontal_offset
                    pos_y = ((img_height - text_height) / 4) + text_vertical_offset
                    center_pos = (int(pos_x), int(pos_y))

                    draw_text_on_image(
                        image,
                        [(str(i), center_pos)],
                        font_path="assets/fonts/Washington.ttf",
                        font_size=46,
                        save=True,
                        save_path=f"assets/generated/icons/resources/core/basic/{str(resource_instance.name).lower()}_{i}.png",
                        outline=True,
                        outline_color=(0, 0, 0, 255),
                        outline_width=1,
                    )

        def generate_static_population_icons():
            from PIL import Image

            from helpers.images import draw_text_on_image

            base_icon: str = f"assets/icons/{tile_set}/resources/core/basic/populationx128.png"
            output_path: str = "assets/generated/icons/resources/core/basic/populationx128_{num}.png"
            font_size: int = 46
            text_vertical_offset = 32
            text_color: Tuple[float, float, float, float] = (0, 0, 0, 1)
            font = ImageFont.truetype("assets/fonts/Washington.ttf", font_size)

            for i in range(1, 50):
                # Open the base image to measure size
                img = Image.open(base_icon).convert("RGBA")
                img_width, img_height = img.size

                text = str(i)

                # Get text bounding box
                bbox = font.getbbox(text)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                # Calculate center position
                pos_x = (img_width - text_width) / 2
                pos_y = ((img_height - text_height) / 2) + text_vertical_offset
                center_pos = (pos_x, pos_y)

                # Draw the text centered
                draw_text_on_image(
                    base_icon,
                    [(text, center_pos)],  # type: ignore
                    font,
                    font_size=font_size,
                    text_color=text_color,
                    save=True,
                    save_path=output_path.format(num=i),
                    outline=True,
                    outline_color=(0, 0, 0, 255),
                    outline_width=1,
                )

        generate_static_resource_icons()
        generate_static_population_icons()

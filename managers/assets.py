from logging import Logger
from os.path import exists
from typing import TYPE_CHECKING, Dict, Optional, Tuple
from zlib import crc32

from direct.gui.OnscreenImage import OnscreenImage
from kivy.core.image import Image as CoreImage
from kivy.resources import resource_find  # type: ignore
from kivy.uix.image import Image as KivyImage
from panda3d.core import NodePath, TextFont, Texture
from PIL import Image

from gameplay.resources.core.basic.culture import Culture
from gameplay.resources.core.basic.faith import Faith
from gameplay.resources.core.basic.food import Food
from gameplay.resources.core.basic.gold import Gold
from gameplay.resources.core.basic.production import Production
from gameplay.resources.core.basic.science import Science
from mixins.singleton import Singleton

if TYPE_CHECKING:
    from main import SCIV


class AssetManager(Singleton):
    texture_cache: Dict[str, Texture] = {}
    font_cache: Dict[str, TextFont] = {}
    model_cache: Dict[str, NodePath] = {}
    kivy_image_cache: Dict[str, CoreImage] = {}

    base: Optional["SCIV"] = None
    _logger: Optional[Logger] = None

    def __setup__(self):
        if self._logger is None and self.base is not None:
            self._logger = self.base.logger.engine.getChild("manager.asset")

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

        cls.logger().debug(f"Loading model {path}")

        if cls.base is None:
            raise ValueError("Base not set for AssetManager")

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
        cls, path: str, size_hint_y: Optional[float] = None, height: Optional[float] = None, use_cache: bool = True
    ) -> KivyImage:
        resolved_path: str = resource_find(path)  # type: ignore
        if not resolved_path:
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
    def set_base(cls, base: "SCIV") -> None:
        cls.base = base

    @classmethod
    def _calculate_cache_key(cls, path: str) -> str:
        return str(crc32(path.encode()))

    @classmethod
    def generate_static_assets(cls):
        def generate_static_resource_icons():
            from helpers.images import create_stacked_horizontal_images

            basic_resources = Gold, Production, Food, Faith, Science, Culture
            for resource in basic_resources:
                resource_instance = resource()
                icon_path = resource_instance.icon
                if not icon_path:
                    continue

                image = Image.open(icon_path).convert("RGBA")

                # Create a stacked horizontal image with the icon
                for i in range(1, 6):
                    stacked_image = create_stacked_horizontal_images([image] * i, offset=(17, 0))
                    stacked_image.save(
                        f"assets/icons/resources/core/basic/{str(resource_instance.name).lower()}_{i}.png"
                    )

        generate_static_resource_icons()

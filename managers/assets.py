from logging import Logger
from typing import TYPE_CHECKING, Dict, Optional, Tuple
from zlib import crc32

from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import NodePath, TextFont, Texture

from mixins.singleton import Singleton

if TYPE_CHECKING:
    from main import SCIV


class AssetManager(Singleton):
    texture_cache: Dict[str, Texture] = {}
    font_cache: Dict[str, TextFont] = {}
    model_cache: Dict[str, NodePath] = {}

    base: Optional["SCIV"] = None
    _logger: Optional[Logger] = None

    def __setup__(self):
        if self._logger is None and self.base is not None and self.base.logger is not None:
            self._logger = self.base.logger.engine.getChild("manager.asset")

    @classmethod
    def logger(cls) -> Logger:
        if cls._logger is None and cls.base is not None and cls.base.logger is not None:
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
            return cls.model_cache[cache_key].copyTo(NodePath())

        cls.logger().debug(f"Loading model {path}")

        if cls.base is None:
            raise ValueError("Base not set for AssetManager")

        model: NodePath = cls.base.loader.load_model(path)

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
            texture = cls.texture_cache[cache_key]
        else:
            cls.logger().debug(f"Loading image {path}")
            if cls.base is None:
                raise ValueError("Base not set for AssetManager")

            texture = cls.base.loader.load_texture(path)

            if texture is None:
                raise ValueError(f"Failed to load texture from {path}")

            if use_cache:
                cls.texture_cache[cache_key] = texture

        # Create a new OnscreenImage instance with the cached texture
        image = OnscreenImage(image=texture)

        if resize:
            image.setScale(
                resize[0] / image.getTexture().getOrigFileXSize(), 1, resize[1] / image.getTexture().getOrigFileYSize()
            )

        return image

    @classmethod
    def set_base(cls, base: "SCIV") -> None:
        cls.base = base

    @classmethod
    def _calculate_cache_key(cls, path: str) -> str:
        return str(crc32(path.encode()))

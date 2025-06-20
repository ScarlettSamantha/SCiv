import json
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from kivy.core.image import Image as CoreImage
from kivy.core.image import Texture as KivyTexture
from kivy.uix.image import Image as KivyImage
from panda3d.core import PNMImage, StringStream, Texture  # type: ignore
from PIL import Image

from managers.assets import AssetManager
from sciv.helpers.windows import WindowsHelper


class AtlasGenerator:
    def __init__(
        self,
        input_dir: List[Path] | Path,
        output_image: Path,
        output_mapping: Path,
        icon_size: Tuple[int, int] = (256, 256),
        max_icons: int = 512,
        atlas_columns: int = 16,
        cache_sub_path: str = "cache",
    ):
        self.input_dir = input_dir if isinstance(input_dir, list) else [input_dir]
        self.output_image = output_image
        self.output_mapping = output_mapping
        self.icon_size = icon_size
        self.max_icons = max_icons
        self.atlas_columns = atlas_columns
        self.cache_sub_path = cache_sub_path
        self._cache_file: Path = (self.output_image.parent / self.cache_sub_path / self.output_image.name).with_suffix(
            ".txo"
        )
        self.is_loaded: bool = False

        self._manifest_cache: Optional[Dict[str, Dict[str, Any] | Any]] = None
        self._atlas_image_cache: Optional[Image.Image] = None
        self._p3d_texture_cache: Optional[Texture] = None
        self._individual_texture_cache: Dict[str, Texture] = {}

    def pre_run(self):
        AssetManager.get_singleton_instance().generate_static_assets()

    def exists(self) -> bool:
        return self.output_image.exists() and self.output_mapping.exists()

    def clear(self) -> None:
        if self.exists():
            self.output_image.unlink(missing_ok=True)
            self.output_mapping.unlink(missing_ok=True)

        self._manifest_cache = None
        self._atlas_image_cache = None
        self._p3d_texture_cache = None
        self._individual_texture_cache.clear()

    def get_panda3d_texture(self, force: bool = False) -> Texture:
        if not self._p3d_texture_cache or force:
            if not self._cache_file.exists():
                self._generate_panda3d_texture()
            else:
                self._load_cached_textures()
        return self._p3d_texture_cache  # type: ignore

    def load_caches(self) -> None:
        """
        Load the atlas texture and mapping from cache files.
        This is used to avoid rebuilding the atlas if it already exists.
        """
        if not self._cache_file.exists():
            raise FileNotFoundError(f"Cache file does not exist: {self._cache_file}")

        self._load_cached_textures()
        self._load_individual_textures()
        self._manifest_cache = self._load_output_mapping()
        self._atlas_image_cache = self._load_output_image()
        self.is_loaded = True

    def save_caches(self) -> None:
        self._dump_cached_textures()
        self._dump_individual_textures()

    def remove(self) -> None:
        """
        Remove the atlas and its cache files.
        If `from_disk` is True, it will also remove the cache files.
        """
        if self.exists():
            self.clear()

        self.output_image.unlink(missing_ok=True)
        self.output_mapping.unlink(missing_ok=True)

        for file in self._cache_file.parent.glob("*.txo"):
            file.unlink(missing_ok=True)

        self._manifest_cache = None
        self._atlas_image_cache = None
        self._p3d_texture_cache = None
        self._individual_texture_cache.clear()
        self.is_loaded = False

    def _generate_panda3d_sub_texture(self, x: int, y: int, w: int, h: int) -> Texture:
        atlas = self.atlas_image

        cropped = atlas.crop((x, y, x + w, y + h))
        buf = BytesIO()
        cropped.save(buf, format="PNG")
        buf.seek(0)
        pnm = PNMImage()

        if not pnm.read(StringStream(buf.read())):
            raise RuntimeError("PNMImage.read failed")

        tex = Texture()
        tex.load(pnm)

        return tex

    def _generate_individual_textures(self) -> None:
        if not self._atlas_image_cache:
            raise ValueError("Atlas image cache is not set. Run `run()` first.")

        if not self._manifest_cache:
            raise ValueError("Manifest cache is not set. Run `run()` first.")

        for key, entry in self._manifest_cache.items():
            x, y = entry["atlas_x"], entry["atlas_y"]
            w, h = entry["width"], entry["height"]
            texture: Texture = self._generate_panda3d_sub_texture(x, y, w, h)

            self._individual_texture_cache[key] = texture  # type: ignore

    def _dump_individual_textures(self) -> None:
        if not self._individual_texture_cache:
            raise ValueError("No individual textures to dump.")

        for key, texture in self._individual_texture_cache.items():
            bam_bytes = texture.encode_to_bam_stream()
            cache_file = self._cache_file.parent / f"{key}.txo"
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_bytes(bam_bytes)

    def _load_individual_textures(self) -> None:
        if not self._cache_file.parent.exists():
            raise FileNotFoundError(f"Cache directory does not exist: {self._cache_file.parent}")

        for cache_file in self._cache_file.parent.glob("*.txo"):
            with open(cache_file, "rb") as f:
                data = f.read()
                if not data:
                    raise ValueError(f"Cache file {cache_file} is empty or invalid.")

            # Deserialize the cache file into a Texture object
            tex: Texture = Texture.decode_from_bam_stream(data)  # type: ignore
            tex.set_loaded_from_txo(True)  # type: ignore
            key = cache_file.stem
            self._individual_texture_cache[key] = tex  # type: ignore

    def get_pil_image_by_virtual_path(self, virtual_path: str) -> Optional[Image.Image]:
        if WindowsHelper.is_windows():
            virtual_path = WindowsHelper.win32_to_unix_path(virtual_path)
        entry = self.lookup_by_virtual_path(virtual_path)
        if not entry:
            return None

        atlas = self.atlas_image
        box = (
            entry["atlas_x"],
            entry["atlas_y"],
            entry["atlas_x"] + entry["width"],
            entry["atlas_y"] + entry["height"],
        )
        cropped = atlas.crop(box)

        return cropped.convert("RGBA")

    def _generate_panda3d_texture(self) -> Texture:
        atlas = self.atlas_image  # PIL.Image
        buf = BytesIO()
        atlas.save(buf, format="PNG")
        buf.seek(0)

        pnm = PNMImage()
        if not pnm.read(StringStream(buf.read())):
            raise RuntimeError("PNMImage.read failed")

        tex = Texture()
        tex.load(pnm)

        bam_bytes = tex.encodeToBamStream()
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache_file.write_bytes(bam_bytes)

        # reapply your filters / wrap modes
        tex.setFormat(Texture.F_srgb_alpha)
        tex.setMinfilter(Texture.FT_linear_mipmap_linear)
        tex.setMagfilter(Texture.FT_linear)
        tex.setWrapU(Texture.WM_clamp)
        tex.setWrapV(Texture.WM_clamp)

        self._p3d_texture_cache = tex

        return self._p3d_texture_cache

    def _load_cached_textures(self) -> None:
        if not self._cache_file.exists():
            raise FileNotFoundError(f"Cache file does not exist: {self._cache_file}")

        with open(self._cache_file, "rb") as f:
            data = f.read()
            if not data:
                raise ValueError("Cache file is empty or invalid.")

        # Deserialize the cache file into a Texture object
        self._p3d_texture_cache = Texture.decode_from_bam_stream(data)  # type: ignore
        self._p3d_texture_cache.set_loaded_from_txo(True)  # type: ignore

    def _dump_cached_textures(self) -> None:
        if self._p3d_texture_cache is None:
            raise ValueError("No texture to dump to cache.")

        bam_bytes = self._p3d_texture_cache.encode_to_bam_stream()
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache_file.write_bytes(bam_bytes)

    def _load_output_mapping(self) -> Dict[str, Dict[str, Any] | Any]:
        if not self.output_mapping.exists():
            raise FileNotFoundError(f"Output mapping file does not exist: {self.output_mapping}")
        with open(self.output_mapping, "r") as f:
            return json.load(f)

    def _load_output_image(self) -> Image.Image:
        if not self.output_image.exists():
            raise FileNotFoundError(f"Output image file does not exist: {self.output_image}")
        return Image.open(self.output_image).convert("RGBA")

    def load(self) -> None:
        if not self.exists():
            raise FileNotFoundError(f"Atlas files do not exist: {self.output_image}, {self.output_mapping}")

        self.clear()

        self._manifest_cache = self._load_output_mapping()
        self._atlas_image_cache = self._load_output_image()

    def run(self, force: bool = False) -> None:
        self.pre_run()

        if not force and self.output_image.exists() and self.output_mapping.exists():
            input_mtime = max(p.stat().st_mtime for d in self.input_dir for p in d.glob("**/*.png"))
            atlas_mtime = self.output_image.stat().st_mtime
            manifest_mtime = self.output_mapping.stat().st_mtime
            if atlas_mtime > input_mtime and manifest_mtime > input_mtime and not force:
                return

        icon_files = sorted(
            icon_file for dir_path in self.input_dir for icon_file in dir_path.glob("**/*.png")
        ) + sorted(icon_file for dir_path in self.input_dir for icon_file in dir_path.glob("*.png"))
        atlas_rows = (min(len(icon_files), self.max_icons) + self.atlas_columns - 1) // self.atlas_columns
        atlas_width = self.atlas_columns * self.icon_size[0]
        atlas_height = atlas_rows * self.icon_size[1]

        atlas = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))
        manifest: Dict[str, Dict[str, Any] | Any] = {}

        for idx, icon_file in enumerate(icon_files[: self.max_icons]):
            icon = Image.open(icon_file).convert("RGBA")
            icon.thumbnail(self.icon_size, Image.Resampling.LANCZOS)
            padded = Image.new("RGBA", self.icon_size, (0, 0, 0, 0))
            offset = ((self.icon_size[0] - icon.width) // 2, (self.icon_size[1] - icon.height) // 2)
            padded.paste(icon, offset)

            x = (idx % self.atlas_columns) * self.icon_size[0]
            y = (idx // self.atlas_columns) * self.icon_size[1]
            atlas.paste(padded, (x, y))

            # resource_key = self._resource_key_from_path(icon_file)

            base_dir = next((d for d in self.input_dir if d in icon_file.parents), None)
            if base_dir is None:
                raise ValueError(f"Could not determine base directory for {icon_file}")

            virtual_path = str(icon_file.relative_to(base_dir))
            full_path = str(icon_file)

            if WindowsHelper.is_windows():
                virtual_path = WindowsHelper.win32_to_unix_path(virtual_path)
                full_path = WindowsHelper.win32_to_unix_path(full_path)

            manifest[virtual_path] = {
                "index": idx,
                "virtual_path": virtual_path,
                "full_path": full_path,
                "atlas_x": x,
                "atlas_y": y,
                "width": self.icon_size[0],
                "height": self.icon_size[1],
            }

        self.output_image.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(self.output_image)
        with open(self.output_mapping, "w") as f:
            json.dump(manifest, f, indent=4)

        self._manifest_cache = manifest
        self._atlas_image_cache = atlas
        self._p3d_texture_cache = None
        self._individual_texture_cache.clear()  # type: ignore
        self.is_loaded = True

        self._generate_individual_textures()
        self._generate_panda3d_texture()

        self.save_caches()

    def _resource_key_from_path(self, path: Path) -> str:
        return path.stem.replace("hex_border_", "resource.core.bonus.")

    @property
    def manifest(self) -> Dict[str, Dict[str, Any] | Any] | None:
        if self._manifest_cache is None:
            with open(self.output_mapping, "r") as f:
                self._manifest_cache = json.load(f)
        return self._manifest_cache

    @property
    def atlas_image(self) -> Image.Image:
        if self._atlas_image_cache is None:
            self._atlas_image_cache = Image.open(self.output_image).convert("RGBA")
        return self._atlas_image_cache

    def lookup_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        return self.manifest.get(key)  # type: ignore

    def lookup_by_virtual_path(self, virtual_path: str) -> Optional[Dict[str, Any]]:
        if "assets/icons/" in virtual_path:
            virtual_path = virtual_path.replace("assets/icons/", "")

        for k, entry in self.manifest.items():  # type: ignore
            if entry["virtual_path"] == virtual_path:
                return self.lookup_by_key(k)

        return None

    def get_kivy_image(self, key: str) -> Optional[KivyImage]:
        entry = self.lookup_by_key(key)
        if not entry:
            return None

        atlas = self.atlas_image
        box = (
            entry["atlas_x"],
            entry["atlas_y"],
            entry["atlas_x"] + entry["width"],
            entry["atlas_y"] + entry["height"],
        )
        cropped = atlas.crop(box)

        buf = BytesIO()
        cropped.save(buf, format="PNG")
        buf.seek(0)

        kivy_tex: KivyTexture = CoreImage(buf, ext="png").texture  # type: ignore
        return KivyImage(texture=kivy_tex)

    def get_coreimage_by_key(self, key: str) -> Optional[CoreImage]:
        entry = self.lookup_by_key(key)
        if not entry:
            return None

        atlas = self.atlas_image
        box = (
            entry["atlas_x"],
            entry["atlas_y"],
            entry["atlas_x"] + entry["width"],
            entry["atlas_y"] + entry["height"],
        )
        cropped = atlas.crop(box)

        buf = BytesIO()
        cropped.save(buf, format="PNG")
        buf.seek(0)

        return CoreImage(buf, ext="png")

    def get_coreimage_by_virtual_path(self, virtual_path: str) -> Optional[CoreImage]:
        entry = self.lookup_by_virtual_path(virtual_path)
        if not entry:
            return None

        if self.manifest is None:
            return None

        key = next((k for k, v in self.manifest.items() if v == entry), None)
        if key:
            return self.get_coreimage_by_key(key)
        return None

    def get_panda3d_texture_by_key(self, key: str) -> Texture:  # type: ignore
        if key in self._individual_texture_cache:
            return self._individual_texture_cache[key]

        entry = self.lookup_by_key(key)
        if not entry:
            raise ValueError(f"Key {key} not found in manifest.")

        sub_texture: Texture = self._generate_panda3d_sub_texture(
            entry["atlas_x"],
            entry["atlas_y"],
            entry["width"],
            entry["height"],
        )

        self._individual_texture_cache[key] = sub_texture
        return self._individual_texture_cache[key]

    def get_panda3d_texture_by_virtual_path(self, virtual_path: str) -> Optional[Texture]:  # type: ignore
        if self.manifest is None:
            return None
        entry = self.manifest.get(virtual_path, None)
        if entry:
            key = next(iter(k for k, v in self.manifest.items() if v == entry), None)
            if key:
                return self.get_panda3d_texture_by_key(key)  # type: ignore
        return None

    def get_index_for_virtual_path(self, virtual_path: str) -> Optional[int]:
        entry = self.lookup_by_virtual_path(virtual_path)
        if entry:
            return entry.get("index")
        return None

    def get_key_for_virtual_path(self, key: str) -> Optional[str]:
        entry = self.lookup_by_key(key)
        if entry:
            return entry.get("virtual_path")
        return None

    def get_position_for_virtual_path(self, virtual_path: str) -> Optional[Tuple[int, int]]:
        entry = self.lookup_by_virtual_path(virtual_path)
        if entry:
            return entry["atlas_x"], entry["atlas_y"]
        return None

    def get_dimensions_for_virtual_path(self, virtual_path: str) -> Optional[Tuple[int, int]]:
        if WindowsHelper.is_windows():
            virtual_path = WindowsHelper.win32_to_unix_path(virtual_path)
        entry = self.lookup_by_virtual_path(virtual_path)
        if entry:
            return entry["width"], entry["height"]
        return None

    def get_dimensions_for_key(self, key: str) -> Optional[Tuple[int, int]]:
        entry = self.lookup_by_key(key)
        if entry:
            return entry["width"], entry["height"]
        return None

    def get_real_path_for_virtual_path(self, virtual_path: str) -> Optional[Path]:
        if WindowsHelper.is_windows():
            virtual_path = WindowsHelper.win32_to_unix_path(virtual_path)
        entry = self.lookup_by_virtual_path(virtual_path)
        if entry:
            full_path = entry.get("full_path")
            if full_path:
                return Path(full_path)
        return None

    def get_dimensions_for_index(self, index: int) -> Optional[Tuple[int, int]]:
        if self.manifest is None:
            return None
        for entry in self.manifest.values():
            if entry["index"] == index:
                return entry["width"], entry["height"]
        return None

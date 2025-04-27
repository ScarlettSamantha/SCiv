import json
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from kivy.core.image import Image as CoreImage
from kivy.core.image import Texture as KivyTexture
from kivy.uix.image import Image as KivyImage
from panda3d.core import PNMImage, StringStream, Texture
from PIL import Image

from managers.assets import AssetManager


class AtlasGenerator:
    def __init__(
        self,
        input_dir: List[Path] | Path,
        output_image: Path,
        output_mapping: Path,
        icon_size: Tuple[int, int] = (128, 128),
        max_icons: int = 512,
        atlas_columns: int = 16,
    ):
        self.input_dir = input_dir if isinstance(input_dir, list) else [input_dir]
        self.output_image = output_image
        self.output_mapping = output_mapping
        self.icon_size = icon_size
        self.max_icons = max_icons
        self.atlas_columns = atlas_columns

        self._manifest_cache: Optional[Dict[str, Dict[str, Any] | Any]] = None
        self._atlas_image_cache: Optional[Image.Image] = None
        self._p3d_texture_cache: Optional[Texture] = None
        self._individual_texture_cache: Dict[str, Texture] = {}

    def pre_run(self):
        AssetManager.get_singleton_instance().generate_static_assets()

    def run(self, force: bool = False) -> None:
        self.pre_run()

        if not force and self.output_image.exists() and self.output_mapping.exists():
            input_mtime = max(p.stat().st_mtime for d in self.input_dir for p in d.glob("**/*.png"))
            atlas_mtime = self.output_image.stat().st_mtime
            manifest_mtime = self.output_mapping.stat().st_mtime
            if atlas_mtime > input_mtime and manifest_mtime > input_mtime:
                return

        icon_files = sorted(icon_file for dir_path in self.input_dir for icon_file in dir_path.glob("**/*.png"))
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

            resource_key = self._resource_key_from_path(icon_file)

            base_dir = next((d for d in self.input_dir if icon_file.is_relative_to(d)), None)
            if base_dir is None:
                raise ValueError(f"Could not determine base directory for {icon_file}")

            virtual_path = str(icon_file.relative_to(base_dir))

            manifest[resource_key] = {
                "index": idx,
                "virtual_path": virtual_path,
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
        self._individual_texture_cache.clear()

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
        if self.manifest is None:
            return None
        return self.manifest.get(key)

    def lookup_by_virtual_path(self, virtual_path: str) -> Optional[Dict[str, Any]]:
        if self.manifest is None:
            return None
        if "assets/icons/" in virtual_path:
            virtual_path = virtual_path.replace("assets/icons/", "")

        for k, entry in self.manifest.items():
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

    def get_panda3d_texture(self) -> Texture:
        if self._p3d_texture_cache is None:
            atlas = self.atlas_image  # a PIL.Image
            buf = BytesIO()
            atlas.save(buf, format="PNG")
            buf.seek(0)

            pnm = PNMImage()
            sstream = StringStream(buf.read())
            if not pnm.read(sstream):  # type: ignore
                raise RuntimeError("Failed to read atlas PNG data into PNMImage.")

            tex = Texture()
            tex.load(pnm)  # type: ignore
            self._p3d_texture_cache = tex  # type: ignore
        return self._p3d_texture_cache

    def get_panda3d_texture_by_key(self, key: str) -> Optional[Texture]:
        if key in self._individual_texture_cache:
            return self._individual_texture_cache[key]

        entry = self.lookup_by_key(key)
        if not entry:
            raise ValueError(f"Key {key} not found in manifest.")

        atlas = self.atlas_image
        box = (
            entry["atlas_x"],
            entry["atlas_y"],
            entry["atlas_x"] + entry["width"],
            entry["atlas_y"] + entry["height"],
        )
        cropped = atlas.crop(box)

        arr = np.array(cropped)
        height, width = arr.shape[:2]
        has_alpha = arr.shape[2] == 4

        # Create and fill PNMImage
        pnm = PNMImage(width, height, 4 if has_alpha else 3)
        for y in range(height):
            for x in range(width):
                r, g, b = arr[y, x][:3]
                a = arr[y, x][3] if has_alpha else 255
                pnm.setXelA(x, y, r / 255, g / 255, b / 255, a / 255)

        tex = Texture()
        tex.load(pnm)  # type: ignore
        self._individual_texture_cache[key] = tex
        return tex

    def get_panda3d_texture_by_virtual_path(self, virtual_path: str) -> Optional[Texture]:
        entry = self.lookup_by_virtual_path(virtual_path)
        if self.manifest is None:
            return None
        if entry:
            key = next((k for k, v in self.manifest.items() if v == entry), None)
            if key:
                return self.get_panda3d_texture_by_key(key)
        return None

    def get_index_for_virtual_path(self, virtual_path: str) -> Optional[int]:
        entry = self.lookup_by_virtual_path(virtual_path)
        if entry:
            return entry.get("index")
        return None

    def get_position_for_virtual_path(self, virtual_path: str) -> Optional[Tuple[int, int]]:
        entry = self.lookup_by_virtual_path(virtual_path)
        if entry:
            return entry["atlas_x"], entry["atlas_y"]
        return None

    def get_dimensions_for_virtual_path(self, virtual_path: str) -> Optional[Tuple[int, int]]:
        entry = self.lookup_by_virtual_path(virtual_path)
        if entry:
            return entry["width"], entry["height"]
        return None

    def get_dimensions_for_key(self, key: str) -> Optional[Tuple[int, int]]:
        entry = self.lookup_by_key(key)
        if entry:
            return entry["width"], entry["height"]
        return None

    def get_dimensions_for_index(self, index: int) -> Optional[Tuple[int, int]]:
        if self.manifest is None:
            return None
        for entry in self.manifest.values():
            if entry["index"] == index:
                return entry["width"], entry["height"]
        return None

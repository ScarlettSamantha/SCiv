import json
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from helpers.cache import Cache
from helpers.os import WindowsHelper
from helpers.paths import PathsHelper
from kivy.core.image import Image as CoreImage
from kivy.core.image import Texture as KivyTexture  # type: ignore
from kivy.uix.image import Image as KivyImage
from panda3d.core import Filename, PNMImage, StringStream, Texture, VirtualFileSystem  # type: ignore
from PIL import Image
from system.asset_archive import P3DAssetArchive  # type: ignore


class AtlasGenerator:
    def __init__(
        self,
        input: List[Path] | Path,
        output_image: Path,
        output_mapping: Path,
        icon_size: Tuple[int, int] = (256, 256),
        max_icons: int = 1048,
        atlas_columns: int = 16,
        cache_sub_path: str = "cache",
    ):
        self.input: List[Path] = input if isinstance(input, list) else [input]
        self._mf_path: Optional[Path] = next((p for p in self.input if p.suffix.lower() == ".mf"), None)
        self.multifile_mode: bool = bool(self._mf_path and self._mf_path.exists())
        self.output_image: Path = output_image
        self.output_mapping: Path = output_mapping
        self.icon_size: Tuple[int, int] = icon_size
        self.max_icons: int = max_icons
        self.atlas_columns: int = atlas_columns
        self.cache_sub_path: str = cache_sub_path
        self._cache_file: Path = (self.output_image.parent / self.cache_sub_path / self.output_image.name).with_suffix(
            ".txo"
        )
        self.is_loaded: bool = False

        self._manifest_cache: Optional[Dict[str, Dict[str, Any] | Any]] = None
        self._atlas_image_cache: Optional[Image.Image] = None
        self._p3d_texture_cache: Optional[Texture] = None
        self._individual_texture_cache: Dict[str, Texture] = {}

        self._archive: Optional[Any] = None
        self._generated_root: Optional[Path] = None

    def _refresh_mf_mode(self) -> None:
        if self._mf_path is not None:
            self.multifile_mode = self._mf_path.suffix.lower() == ".mf" and self._mf_path.exists()

    def pre_run(self) -> None:
        from managers.assets import AssetManager

        AssetManager.get_singleton_instance().generate_static_assets()
        self._generated_root = Path(PathsHelper.get_data_dir()) / "assets" / "generated"
        self._refresh_mf_mode()
        if self.multifile_mode and self._mf_path:
            try:
                self._archive = P3DAssetArchive.mount_only(self._mf_path, mount_point="/", prefix=None)  # type: ignore
            except Exception:
                vfs: VirtualFileSystem = VirtualFileSystem.getGlobalPtr()
                vfs.mount(Filename.from_os_specific(str(self._mf_path)), ".", VirtualFileSystem.MFReadOnly)

    def exists(self) -> bool:
        return self.output_image.exists() and self.output_mapping.exists()

    def clear(self) -> None:
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
            if hasattr(texture, "encode_to_bam_stream"):
                bam_bytes = texture.encode_to_bam_stream()  # type: ignore
            else:
                bam_bytes = texture.encodeToBamStream()  # type: ignore
            cache_file = self._cache_file.parent / f"{key}.txo"
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_bytes(bam_bytes)

    def _load_individual_textures(self) -> None:
        if not self._cache_file.parent.exists():
            raise FileNotFoundError(f"Cache directory does not exist: {self._cache_file.parent}")
        for cache_file in self._cache_file.parent.glob("*.txo"):
            if cache_file == self._cache_file:
                continue
            data: bytes = cache_file.read_bytes()
            if not data:
                raise ValueError(f"Cache file {cache_file} is empty or invalid.")
            tex: Texture = Texture.decode_from_bam_stream(data)  # type: ignore
            tex.set_loaded_from_txo(True)  # type: ignore
            self._individual_texture_cache[cache_file.stem] = tex  # type: ignore

    def get_pil_image_by_virtual_path(self, virtual_path: str) -> Optional[Image.Image]:
        if WindowsHelper.is_windows():
            virtual_path = WindowsHelper.win32_to_unix_path(virtual_path)
        entry: Dict[str, Any] | None = self.lookup_by_virtual_path(virtual_path)
        if not entry:
            return None
        atlas: Image.Image = self.atlas_image
        box: Tuple[int, int, int, int] = (
            entry["atlas_x"],
            entry["atlas_y"],
            entry["atlas_x"] + entry["width"],
            entry["atlas_y"] + entry["height"],
        )
        cropped: Image.Image = atlas.crop(box)
        return cropped.convert("RGBA")

    def _generate_panda3d_texture(self) -> Texture:
        atlas: Image.Image = self.atlas_image
        buf = BytesIO()
        atlas.save(buf, format="PNG")
        buf.seek(0)
        pnm = PNMImage()
        if not pnm.read(StringStream(buf.read())):
            raise RuntimeError("PNMImage.read failed")
        tex = Texture()
        tex.load(pnm)
        if hasattr(tex, "encodeToBamStream"):
            bam_bytes: bytes = tex.encodeToBamStream()  # type: ignore
        else:
            bam_bytes = tex.encode_to_bam_stream()  # type: ignore
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache_file.write_bytes(bam_bytes)
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
        data: bytes = self._cache_file.read_bytes()
        if not data:
            raise ValueError("Cache file is empty or invalid.")
        self._p3d_texture_cache = Texture.decode_from_bam_stream(data)  # type: ignore
        self._p3d_texture_cache.set_loaded_from_txo(True)  # type: ignore

    def _dump_cached_textures(self) -> None:
        if self._p3d_texture_cache is None:
            raise ValueError("No texture to dump to cache.")
        if hasattr(self._p3d_texture_cache, "encode_to_bam_stream"):
            bam_bytes: bytes = self._p3d_texture_cache.encode_to_bam_stream()  # type: ignore
        else:
            bam_bytes = self._p3d_texture_cache.encodeToBamStream()  # type: ignore
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

    def _list_pngs_from_multifile(self) -> List[str]:
        paths: List[str] = []
        if P3DAssetArchive and self._archive:
            for name in self._archive.list():  # type: ignore
                n: str = name.lstrip("/")  # type: ignore
                if n.lower().endswith(".png"):  # type: ignore
                    paths.append(n)  # type: ignore
            return sorted(paths)
        mf = None
        try:
            from panda3d.core import Multifile  # type: ignore

            mf = Multifile()
            if mf.openRead(multifile_name=str(self._mf_path)):  # type: ignore
                n: int = mf.getNumSubfiles()
                for i in range(n):
                    name = mf.getSubfileName(i).lstrip("/")
                    if name.lower().endswith(".png"):
                        paths.append(name)
        finally:
            if mf is not None:
                mf.close()
        return sorted(paths)

    def _list_generated_pngs(self) -> List[Path]:
        out: List[Path] = []
        if not self._generated_root or not self._generated_root.exists():
            return out
        for p in sorted(self._generated_root.rglob("*.png")):
            if p.is_file():
                out.append(p)
        return out

    def _latest_generated_mtime(self) -> float:
        latest: float = 0.0
        for p in self._list_generated_pngs():
            try:
                mt: float = p.stat().st_mtime
            except Exception:
                mt = 0.0
            if mt > latest:
                latest = mt
        return latest

    def _read_png_from_multifile(self, virtual_path: str) -> bytes:
        if P3DAssetArchive and self._archive:
            return self._archive.read_bytes(virtual_path)  # type: ignore
        vfs: VirtualFileSystem = VirtualFileSystem.getGlobalPtr()
        data = vfs.readFile(Filename(virtual_path), False)  # type: ignore
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)
        if isinstance(data, str):
            return data.encode("utf-8")
        mv: memoryview[Any] = memoryview(data)  # type: ignore
        return mv.tobytes()

    def _first_existing_icon(self, icon_rel: str, tile_set: str = "default") -> Optional[str]:
        assets: P3DAssetArchive = Cache.get_asset_archive()
        ic = icon_rel.lstrip("/")
        cand: List[str] = []
        if ic.startswith("assets/"):
            cand.append(ic)

        seen: Set[str] = set()
        for c in cand:
            if c in seen:
                continue
            seen.add(c)
            try:
                assets.read_bytes(c)
                return c
            except Exception:
                continue
        return None

    def _normalize_generated_virtual_path(self, pth: Path) -> str:
        data_root: Path = Path(PathsHelper.get_data_dir()).resolve()
        if pth.is_relative_to(data_root):  # type: ignore
            return pth.relative_to(data_root).as_posix()
        return pth.as_posix()

    def run(self, force: bool = False) -> None:
        self.pre_run()
        self._generated_root = Path(PathsHelper.get_data_dir()) / "assets" / "generated"
        self._refresh_mf_mode()

        if not force and self.output_image.exists() and self.output_mapping.exists():
            fs_pngs: Set[Path] = {p for d in self.input for p in d.glob("**/*.png")}
            fs_mtime: float = max((p.stat().st_mtime for p in fs_pngs), default=0.0)
            gen_paths: List[Path] = (
                list(self._generated_root.rglob("*.png"))
                if self._generated_root and self._generated_root.exists()
                else []
            )
            gen_mtime: float = max((p.stat().st_mtime for p in gen_paths), default=0.0)
            mf_mtime: float = self._mf_path.stat().st_mtime if self._mf_path and self._mf_path.exists() else 0.0
            input_mtime: float = max(fs_mtime, gen_mtime, mf_mtime)
            atlas_mtime: float = self.output_image.stat().st_mtime
            manifest_mtime: float = self.output_mapping.stat().st_mtime
            if atlas_mtime > input_mtime and manifest_mtime > input_mtime:
                self.load()
                return

        mf_pngs: List[str] = self._list_pngs_from_multifile() if self._mf_path and self._mf_path.exists() else []
        gen_pngs: List[Path] = (
            sorted(self._generated_root.rglob("*.png"))
            if self._generated_root and self._generated_root.exists()
            else []
        )
        fs_icons: List[Path] = sorted({p for d in self.input for p in d.glob("**/*.png")})

        if not mf_pngs and not gen_pngs and not fs_icons:
            self.output_image.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(self.output_image)
            with open(self.output_mapping, "w") as f:
                json.dump({}, f, indent=4)
            self.load()
            return

        records: List[Tuple[str, str, Optional[Path]]] = []
        for vp in mf_pngs:
            records.append(("mf", vp, None))
        for p in gen_pngs:
            records.append(("fs_gen", p.as_posix(), p))
        for p in fs_icons:
            records.append(("fs", p.as_posix(), p))

        uniq: Dict[str, Tuple[str, str, Optional[Path]]] = {}
        for kind, s, p in records:
            if kind == "mf":
                vkey: str = s
            else:
                if self._generated_root and p:
                    vkey = self._normalize_generated_virtual_path(p)
                else:
                    base_dir: Optional[Path] = next((d for d in self.input if p and d in p.parents), None)
                    vkey = p.relative_to(base_dir).as_posix() if base_dir and p else s  # type: ignore
            if vkey not in uniq:
                uniq[vkey] = (kind, s, p)

        ordered_keys: List[str] = sorted(uniq.keys())
        take: List[Tuple[str, str, Optional[Path]]] = [uniq[k] for k in ordered_keys][: self.max_icons]

        atlas_rows: int = (len(take) + self.atlas_columns - 1) // self.atlas_columns
        atlas_width: int = self.atlas_columns * self.icon_size[0]
        atlas_height: int = atlas_rows * self.icon_size[1]

        atlas: Image.Image = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))
        manifest: Dict[str, Dict[str, Any]] = {}

        for idx, (kind, src, pth) in enumerate(take):
            if kind == "mf":
                png_bytes: bytes = self._read_png_from_multifile(src)
                with Image.open(BytesIO(png_bytes)).convert("RGBA") as icon:
                    icon.thumbnail(self.icon_size, Image.Resampling.LANCZOS)
                    padded: Image.Image = Image.new("RGBA", self.icon_size, (0, 0, 0, 0))
                    offset: Tuple[int, int] = (
                        (self.icon_size[0] - icon.width) // 2,
                        (self.icon_size[1] - icon.height) // 2,
                    )
                    padded.paste(icon, offset)
            else:
                with Image.open(pth).convert("RGBA") as icon:  # type: ignore
                    icon.thumbnail(self.icon_size, Image.Resampling.LANCZOS)
                    padded = Image.new("RGBA", self.icon_size, (0, 0, 0, 0))
                    offset = (
                        (self.icon_size[0] - icon.width) // 2,
                        (self.icon_size[1] - icon.height) // 2,
                    )
                    padded.paste(icon, offset)

            x: int = (idx % self.atlas_columns) * self.icon_size[0]
            y: int = (idx // self.atlas_columns) * self.icon_size[1]
            atlas.paste(padded, (x, y))

            if kind == "mf":
                virtual_path = src
                full_path: str = f"{self._mf_path.as_posix()}#{src}" if self._mf_path else src
            else:
                if self._generated_root and pth:
                    virtual_path = self._normalize_generated_virtual_path(pth)
                else:
                    base_dir = next((d for d in self.input if pth and d in pth.parents), None)
                    virtual_path = pth.relative_to(base_dir).as_posix() if base_dir and pth else src  # type: ignore
                full_path = pth.as_posix() if pth else src  # type: ignore

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
                "uv": [
                    x / atlas_width,
                    y / atlas_height,
                    (x + self.icon_size[0]) / atlas_width,
                    (y + self.icon_size[1]) / atlas_height,
                ],
                "atlas_size": [atlas_width, atlas_height],
            }

        self.output_image.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(self.output_image)
        with open(self.output_mapping, "w") as f:
            json.dump(manifest, f, indent=4)

        self._manifest_cache = manifest
        self._atlas_image_cache = atlas
        self._p3d_texture_cache = None
        self._individual_texture_cache.clear()
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
        if self.manifest is None:
            return None
        q = virtual_path.replace("\\", "/").lstrip("/")

        if q in self.manifest:
            return self.manifest[q]  # type: ignore

        q_generated = q.replace("assets/", "assets/generated/")
        if q_generated in self.manifest:
            return self.manifest[q_generated]  # type: ignore

        raise ValueError(f"Virtual path {virtual_path} not found in manifest.")

    def get_kivy_image(self, key: str) -> Optional[KivyImage]:
        entry: Dict[str, Any] | None = self.lookup_by_key(key)
        if not entry:
            return None
        atlas: Image.Image = self.atlas_image
        box: Tuple[int, int, int, int] = (
            entry["atlas_x"],
            entry["atlas_y"],
            entry["atlas_x"] + entry["width"],
            entry["atlas_y"] + entry["height"],
        )
        cropped: Image.Image = atlas.crop(box)
        buf = BytesIO()
        cropped.save(buf, format="PNG")
        buf.seek(0)
        kivy_tex: KivyTexture = CoreImage(buf, ext="png").texture  # type: ignore
        return KivyImage(texture=kivy_tex)  # type: ignore

    def get_coreimage_by_key(self, key: str) -> Optional[CoreImage]:
        entry: Dict[str, Any] | None = self.lookup_by_key(key)
        if not entry:
            return None
        atlas: Image.Image = self.atlas_image
        box: Tuple[int, int, int, int] = (
            entry["atlas_x"],
            entry["atlas_y"],
            entry["atlas_x"] + entry["width"],
            entry["atlas_y"] + entry["height"],
        )
        cropped: Image.Image = atlas.crop(box)
        buf = BytesIO()
        cropped.save(buf, format="PNG")
        buf.seek(0)
        return CoreImage(buf, ext="png")

    def get_coreimage_by_virtual_path(self, virtual_path: str) -> Optional[CoreImage]:
        entry: Dict[str, Any] | None = self.lookup_by_virtual_path(virtual_path)
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
        entry: Dict[str, Any] | None = self.lookup_by_key(key)
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
        entry: Dict[str, Any] | None = self.lookup_by_virtual_path(virtual_path)
        if not entry:
            return None
        key: str | None = next((k for k, v in self.manifest.items() if v == entry), None)  # type: ignore
        if not key:
            return None
        return self.get_panda3d_texture_by_key(key)  # type: ignore

    def get_index_for_virtual_path(self, virtual_path: str) -> Optional[int]:
        entry: Dict[str, Any] | None = self.lookup_by_virtual_path(virtual_path)
        if entry:
            return entry.get("index")
        return None

    def get_key_for_virtual_path(self, key: str) -> Optional[str]:
        entry: Dict[str, Any] | None = self.lookup_by_key(key)
        if entry:
            return entry.get("virtual_path")
        return None

    def get_position_for_virtual_path(self, virtual_path: str) -> Optional[Tuple[int, int]]:
        entry: Dict[str, Any] | None = self.lookup_by_virtual_path(virtual_path)
        if entry:
            return entry["atlas_x"], entry["atlas_y"]
        return None

    def get_dimensions_for_virtual_path(self, virtual_path: str) -> Optional[Tuple[int, int]]:
        if WindowsHelper.is_windows():
            virtual_path = WindowsHelper.win32_to_unix_path(virtual_path)
        entry: Dict[str, Any] | None = self.lookup_by_virtual_path(virtual_path)
        if entry:
            return entry["width"], entry["height"]
        return None

    def get_dimensions_for_key(self, key: str) -> Optional[Tuple[int, int]]:
        entry: Dict[str, Any] | None = self.lookup_by_key(key)
        if entry:
            return entry["width"], entry["height"]
        return None

    def get_real_path_for_virtual_path(self, virtual_path: str) -> Optional[Path]:
        if WindowsHelper.is_windows():
            virtual_path = WindowsHelper.win32_to_unix_path(virtual_path)
        entry: Dict[str, Any] | None = self.lookup_by_virtual_path(virtual_path)
        if entry:
            full_path: Any | None = entry.get("full_path")
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

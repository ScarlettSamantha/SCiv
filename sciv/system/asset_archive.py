import os
from io import BytesIO
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, List, Optional, Set, Tuple, cast

from panda3d.core import (  # type: ignore
    Filename,
    Loader,
    Multifile,
    NodePath,
    PandaNode,
    Shader,
    Texture,
    VirtualFileSystem,
    loadPrcFileData,
)
from PIL.ImageFile import ImageFile
from PIL.ImageFont import FreeTypeFont

if TYPE_CHECKING:
    from kivy.uix.image import Image

_SAFE_TEXT_EXTS: Set[str] = {
    ".txt",
    ".prc",
    ".cfg",
    ".ini",
    ".json",
    ".csv",
    ".xml",
    ".md",
    ".glsl",
    ".vert",
    ".frag",
    ".geom",
    ".comp",
    ".shader",
    ".kv",
    ".yaml",
    ".yml",
    ".toml",
    ".gltf",
}

_SAFE_BINARY_EXTS: Set[str] = {
    ".bam",
    ".txo",
    ".pz",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif",
    ".tga",
    ".tif",
    ".tiff",
    ".dds",
    ".ktx",
    ".ktx2",
    ".ogg",
    ".wav",
    ".mp3",
    ".ttf",
    ".otf",
    ".fnt",
    ".glb",
    ".zip",
}

_SAFE_DEFAULT_INCLUDE: Set[str] = _SAFE_TEXT_EXTS | _SAFE_BINARY_EXTS


def _register_ext_tables(text_exts: Iterable[str], bin_exts: Iterable[str]) -> None:
    tx = " ".join(sorted({("." + e.lstrip(".")).lower() for e in text_exts}))
    bx = " ".join(sorted({("." + e.lstrip(".")).lower() for e in bin_exts}))
    if tx:
        loadPrcFileData("", f"text-extensions {tx}")
    if bx:
        loadPrcFileData("", f"binary-extensions {bx}")


class P3DAssetArchive:
    def __init__(
        self,
        input_dirs: List[Path] | Path | None,
        archive_path: Path,
        mount_point: str = "/",
        prefix: Optional[str] = "assets",
        compression: int = 6,
        include_exts: Optional[Set[str]] = None,
        exclude_globs: Optional[List[str]] = None,
        skip_hidden: bool = True,
        skip_no_ext: bool = True,
        password: Optional[str] = None,
        follow_symlinks: bool = True,
    ):
        self.archive_path = Path(archive_path)
        self.mount_point = mount_point.rstrip("/") or "/"
        self.prefix = (prefix or "").strip("/")
        self.compression = max(0, min(9, compression))
        self.password = password

        if isinstance(input_dirs, list):
            self.base_dirs: List[Path] = [Path(p) for p in input_dirs]
        elif isinstance(input_dirs, Path):
            self.base_dirs = [input_dirs]
        else:
            self.base_dirs = []
        print(f"Base dirs: {self.base_dirs}")

        if include_exts is None:
            self.include_exts: Optional[Set[str]] = None
        else:
            self.include_exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in include_exts}

        self.exclude_globs: List[str] = exclude_globs or []
        self.skip_hidden: bool = skip_hidden
        self.skip_no_ext: bool = skip_no_ext
        self.follow_symlinks: bool = follow_symlinks

        self._mounted = False
        _register_ext_tables(_SAFE_TEXT_EXTS, _SAFE_BINARY_EXTS)
        self.vfs: VirtualFileSystem = VirtualFileSystem.getGlobalPtr()

    def exists(self) -> bool:
        return self.archive_path.exists()

    def remove(self) -> None:
        self.unmount()
        self.archive_path.unlink(missing_ok=True)

    def build(self, force: bool = False) -> None:
        print(f"Building asset archive at: {self.archive_path}")
        files: List[Tuple[str, Path]] = self._gather_files()
        mf = Multifile()
        mf.openWrite(multifile_name=str(self.archive_path))

        if self.password:
            mf.setEncryptionFlag(True)
            mf.setEncryptionPassword(self.password)

        for rp, src in files:
            sfn: Filename = Filename.from_os_specific(str(src))
            if src.suffix.lower() in _SAFE_TEXT_EXTS:
                sfn.set_text()
            else:
                sfn.set_binary()

            mf.addSubfile(rp, sfn, self.compression)
        mf.flush()
        mf.close()

    def mount(self, mf_path: str | PathLike[Any], priority: int = 0) -> None:
        vfs: VirtualFileSystem = VirtualFileSystem.getGlobalPtr()
        vfs.mount(Filename(path=mf_path), mount_point=".", flags=VirtualFileSystem.MFReadOnly)
        self.vfs = vfs

    def unmount(self) -> None:
        if not self._mounted:
            return

        vfs: VirtualFileSystem = VirtualFileSystem.getGlobalPtr()
        vfs.unmount(physical_filename=Filename.from_os_specific(os_specific=str(self.archive_path)))
        self._mounted = False

    def list(self) -> List[str]:
        mf = Multifile()
        out: List[str] = []

        if not mf.openRead(multifile_name=str(self.archive_path)):
            return out

        n = mf.getNumSubfiles()

        for i in range(n):
            name = mf.getSubfileName(i)
            out.append(name)

        mf.close()
        out.sort()
        return out

    def read_bytes(self, virtual_path: str) -> bytes:
        for cand in self._candidate_filenames(virtual_path):
            try:
                data = self.vfs.readFile(cand, False)  # type: ignore
            except Exception:
                data = None

            if data is None:
                continue

            if isinstance(data, (bytes, bytearray)):
                return bytes(data)

            if isinstance(data, str):
                return data.encode("utf-8")
            try:
                mv: memoryview[int] = memoryview(data)  # type: ignore
            except Exception:
                continue

            return mv.tobytes()
        raise FileNotFoundError(f"Virtual file not found: {virtual_path}")

    def get_kivy_image_texture(self, virtual_path: str, **kwargs: Any) -> Texture:
        from kivy.core.image import Image as CoreImage

        data: bytes = self.read_bytes(virtual_path)
        ext: str = Path(virtual_path).suffix.lstrip(".").lower()
        ci = CoreImage(BytesIO(data), ext=ext)
        return cast(Texture, ci.texture)  # type: ignore

    def get_kivy_image_object(self, virtual_path: str, **kwargs: Any) -> "Image":
        from kivy.uix.image import Image

        return Image(texture=self.get_kivy_image_texture(virtual_path), **kwargs)

    def get_shader(self, frag: str, vert: str) -> Shader:
        return Shader.load(lang=Shader.SL_GLSL, fragment=frag, vertex=vert)

    def read_text(self, virtual_path: str, encoding: str = "utf-8") -> Optional[str]:
        bytes = self.vfs.read_file(virtual_path, True)  # type: ignore

        if bytes is None:
            return None

        if isinstance(bytes, str):
            return bytes

        try:
            mv: memoryview[int] = memoryview(bytes)  # type: ignore
            return mv.tobytes()  # type: ignore
        except Exception:
            return None

    def ensure(self, mf_path: str, force: bool = False, auto_mount: bool = False, priority: int = 0) -> None:
        self.build(force=force)
        if auto_mount:
            self.mount(mf_path, priority=priority)

    def get_model(self, virtual_path: str) -> "NodePath":
        from helpers.cache import Cache

        loader: Loader = Cache.get_showbase_instance().loader  # type: ignore

        model_tpl: "NodePath[PandaNode] | None" = loader.loadModel(virtual_path)  # type: ignore

        if not model_tpl:
            raise FileNotFoundError(f"Model not found in asset archive: {virtual_path}")

        return model_tpl  # type: ignore

    @classmethod
    def mount_only(
        cls,
        archive_path: Path,
        mount_point: str = "/",
        prefix: Optional[str] = "assets",
        priority: int = 0,
        password: Optional[str] = None,
    ) -> "P3DAssetArchive":
        obj = cls(input_dirs=None, archive_path=archive_path, mount_point=mount_point, prefix=prefix, password=password)
        obj.mount(archive_path, priority=priority)
        return obj

    def _gather_files(self) -> List[Tuple[str, Path]]:
        results: List[Tuple[str, Path]] = []
        print(f"Gathering files from base dirs: {self.base_dirs}")
        for base in self.base_dirs:
            print(f"Scanning base dir: {base}")
            b = Path(base)
            if not b.exists():
                print(f"Base dir does not exist: {b}")
                continue

            for root, dirs, files in os.walk(b, followlinks=self.follow_symlinks):
                root_path = Path(root)

                if self.skip_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith(".")]

                for fname in files:
                    print(f"Checking file: {fname}")
                    if self.skip_hidden and fname.startswith("."):
                        continue
                    p = root_path / fname
                    if not p.is_file():
                        continue

                    if self.skip_no_ext and not p.suffix:
                        continue

                    if self.include_exts is not None:
                        suffixes: List[str] = [s.lower() for s in p.suffixes]
                        if not any(s in self.include_exts for s in suffixes):
                            continue

                    if any(p.match(g) or str(p).endswith(g) for g in self.exclude_globs):
                        continue

                    rel = p.relative_to(b).as_posix()
                    vp = f"{self.prefix}/{rel}" if self.prefix else rel
                    results.append((vp, p))

        return results

    def _candidate_filenames(self, vp: str) -> List[Filename]:
        return [Filename(vp)]

    def get_panda3d_texture(self, virtual_path: str) -> Optional["Texture"]:
        from panda3d.core import Texture

        texture_bytes = self.read_bytes(virtual_path)
        if not texture_bytes:
            return None
        tex = Texture()
        if not tex.read(texture_bytes):
            return None

    def get_panda3d_image(self, virtual_path: str) -> "ImageFile":
        from PIL import Image

        texture_bytes: bytes = self.read_bytes(virtual_path)
        img: ImageFile = Image.open(BytesIO(texture_bytes))
        return img

    def get_freetype_font(self, virtual_path: str, size: int) -> FreeTypeFont:
        data: bytes = self.read_bytes(virtual_path)

        return FreeTypeFont(BytesIO(data), size=size)

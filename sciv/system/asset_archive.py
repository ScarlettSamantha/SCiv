from io import BytesIO
from os import PathLike
from pathlib import Path
from typing import Any, Iterable, List, Optional, Set, Tuple, cast

from helpers.os import WindowsHelper
from kivy.uix.image import Image
from panda3d.core import Filename, Multifile, Texture, VirtualFileSystem, loadPrcFileData  # type: ignore
from PIL.ImageFile import ImageFile
from PIL.ImageFont import FreeTypeFont

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
        self.include_exts: Set[str] = (
            {e.lower() if e.startswith(".") else f".{e.lower()}" for e in include_exts}
            if include_exts
            else set(_SAFE_DEFAULT_INCLUDE)
        )
        self.exclude_globs: List[str] = exclude_globs or []
        self.skip_hidden: bool = skip_hidden
        self.skip_no_ext: bool = skip_no_ext
        self._mounted = False
        _register_ext_tables(_SAFE_TEXT_EXTS, _SAFE_BINARY_EXTS)
        self.vfs: VirtualFileSystem = VirtualFileSystem.getGlobalPtr()

    def exists(self) -> bool:
        return self.archive_path.exists()

    def remove(self) -> None:
        self.unmount()
        self.archive_path.unlink(missing_ok=True)

    def build(self, force: bool = False) -> None:
        if self.archive_path.exists() and not force:
            return
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

        data = self.read_bytes(virtual_path)
        ext = Path(virtual_path).suffix.lstrip(".").lower()
        ci = CoreImage(BytesIO(data), ext=ext)
        return cast(Texture, ci.texture)  # type: ignore

    def get_kivy_image_object(self, virtual_path: str, **kwargs: Any) -> Image:
        return Image(texture=self.get_kivy_image_texture(virtual_path), **kwargs)

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
        for base in self.base_dirs:
            b = Path(base)
            if not b.exists():
                continue
            for p in sorted(b.rglob("*")):
                if not p.is_file():
                    continue
                if self.skip_hidden and p.name.startswith("."):
                    continue
                if self.skip_no_ext and p.suffix == "":
                    continue
                if self.include_exts and p.suffix.lower() not in self.include_exts:
                    continue
                if any(p.match(g) or str(p).endswith(g) for g in self.exclude_globs):
                    continue
                rel = p.relative_to(b).as_posix()
                vp = f"{self.prefix}/{rel}" if self.prefix else rel
                if WindowsHelper.is_windows():
                    vp = WindowsHelper.win32_to_unix_path(vp)
                results.append((vp, p))
        return results

    def _candidate_filenames(self, vp: str) -> List[Filename]:
        mp: str = self.mount_point.rstrip("/") if self.mount_point else ""
        base: str = vp.lstrip("/")
        candidates: List[str] = []

        candidates.append(vp)
        if not vp.startswith("/"):
            candidates.append("/" + vp)
        if mp:
            candidates.append(f"{mp}/{base}")
            candidates.append(f"/{mp}/{base}")

        if base.startswith("icons/") or base.startswith("/icons/"):
            rest = base[len("icons/") :] if base.startswith("icons/") else base[len("/icons/") :]
            icon_variants = [
                f"assets/icons/default/{rest}",
                f"/assets/icons/default/{rest}",
            ]
            if mp:
                icon_variants.extend([f"{mp}/assets/icons/default/{rest}", f"/{mp}/assets/icons/default/{rest}"])
            candidates = icon_variants + candidates

        if base.startswith("resources/"):
            rest = base[len("resources/") :]
            res_variants = [
                f"assets/icons/default/resources/{rest}",
                f"/assets/resources/icons/default/{rest}",
            ]
            if mp:
                res_variants.extend([f"{mp}/assets/icons/default/{rest}", f"/{mp}/assets/icons/default/{rest}"])
            candidates = res_variants + candidates

        seen: Set[str] = set()
        out: List[str] = []
        for c in candidates:
            if c in seen:
                continue
            seen.add(c)
            out.append(c)

        return [Filename(x) for x in out]

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

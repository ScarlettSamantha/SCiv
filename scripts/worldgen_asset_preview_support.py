#!/usr/bin/env python3
"""Asset preview helpers for the standalone worldgen viewer."""

import ast
import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from tempfile import gettempdir

from worldgen_generation_support import REPO_ROOT, SCIV_ROOT, _OFFLINE_RESOURCE_TERRAIN_CLASS_PATHS
from worldgen_viewer_support import resource_display_text, terrain_display_name


_TERRAIN_TEXTURE_ROOTS: tuple[Path, ...] = (
    REPO_ROOT / "assets/terrain/default",
    REPO_ROOT / "assets/terrain/texture",
    REPO_ROOT / "assets/terrain/basic",
)
_RESOURCE_ROOT = SCIV_ROOT / "gameplay" / "resources" / "core"
_MODEL_PREVIEW_CACHE_DIR = Path(gettempdir()) / "sciv-worldgen-model-previews"
_UNSET = object()
_PANDA3D_AVAILABLE = False

try:
    from direct.showbase.ShowBase import ShowBase
    from panda3d.core import AmbientLight, Filename, PNMImage, PerspectiveLens, Point3, PointLight, loadPrcFileData
except Exception:
    ShowBase = None  # type: ignore[assignment]
else:
    loadPrcFileData("", "window-type offscreen")
    loadPrcFileData("", "audio-library-name null")
    loadPrcFileData("", "win-size 320 320")
    loadPrcFileData("", "sync-video false")
    loadPrcFileData("", "show-frame-rate-meter false")
    _PANDA3D_AVAILABLE = True


type PreviewVector = tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class AssetPreviewInfo:
    kind: str
    key: str
    display_name: str
    source_class: str
    primary_image_label: str
    primary_image_path: Path | None
    primary_image_variants: tuple[Path, ...]
    model_path: Path | None
    model_scale: PreviewVector
    model_hpr: PreviewVector
    model_offset: PreviewVector


class _ModelPreviewRenderer(ShowBase):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__(windowType="offscreen")
        self.disableMouse()
        self.setBackgroundColor(0.10, 0.11, 0.13, 1.0)

        lens = PerspectiveLens()
        lens.setFov(38)
        lens.setNearFar(0.01, 1000.0)
        self.cam.node().setLens(lens)

    def render_preview(
        self,
        model_path: Path,
        *,
        scale: PreviewVector,
        hpr: PreviewVector,
        offset: PreviewVector,
        output_path: Path,
    ) -> bool:
        preview_root = self.render.attachNewNode("preview-root")
        ambient_light_np = None
        point_light_np = None

        try:
            model = self.loader.loadModel(Filename.fromOsSpecific(str(model_path)))
            if model is None or model.isEmpty():
                return False

            model.reparentTo(preview_root)
            model.setScale(*scale)
            model.setHpr(*hpr)
            model.setPos(*offset)

            ambient_light = AmbientLight("preview-ambient")
            ambient_light.setColor((0.74, 0.76, 0.80, 1.0))
            ambient_light_np = self.render.attachNewNode(ambient_light)
            self.render.setLight(ambient_light_np)

            point_light = PointLight("preview-point")
            point_light.setColor((0.98, 0.98, 0.98, 1.0))
            point_light_np = self.render.attachNewNode(point_light)
            point_light_np.setPos(4.0, -7.0, 8.0)
            self.render.setLight(point_light_np)

            bounds = model.getTightBounds()
            if bounds is not None:
                min_point, max_point = bounds
                center = (min_point + max_point) * 0.5
                size = max(
                    float(max_point.x - min_point.x),
                    float(max_point.y - min_point.y),
                    float(max_point.z - min_point.z),
                    1.0,
                )
            else:
                center = Point3(0.0, 0.0, 0.0)
                size = 2.0

            distance = max(size * 2.7, 3.0)
            height = max(size * 1.0, 1.9)
            self.cam.setPos(center.x, center.y - distance, center.z + height)
            self.cam.lookAt(center)

            for _ in range(3):
                self.graphicsEngine.renderFrame()

            if self.win is None:
                return False

            image = PNMImage()
            if not self.win.getScreenshot(image):
                return False

            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.write(Filename.fromOsSpecific(str(output_path)))
            return True
        finally:
            if ambient_light_np is not None:
                self.render.clearLight(ambient_light_np)
                ambient_light_np.removeNode()
            if point_light_np is not None:
                self.render.clearLight(point_light_np)
                point_light_np.removeNode()
            preview_root.removeNode()


def preview_path_text(path: Path | None) -> str | None:
    if path is None:
        return None

    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def format_asset_preview_metadata(preview: AssetPreviewInfo) -> str:
    lines = [
        f"Key: {preview.key}",
        f"Class: {preview.source_class}",
    ]

    if preview.model_path is not None:
        lines.append(
            "Model transform: "
            f"scale={preview.model_scale} · hpr={preview.model_hpr} · offset={preview.model_offset}"
        )

    if len(preview.primary_image_variants) > 1:
        variants = ", ".join(path.parent.name for path in preview.primary_image_variants)
        lines.append(f"{preview.primary_image_label} variants: {variants}")

    return "\n".join(lines)


def resolve_terrain_asset_preview(terrain_key: str | None) -> AssetPreviewInfo | None:
    normalized_key = _normalize_identifier(terrain_key)
    if normalized_key is None:
        return None

    return _terrain_previews_by_key().get(normalized_key)


def resolve_resource_asset_preview(resource_key: str | None, *, is_water: bool) -> AssetPreviewInfo | None:
    normalized_key = resource_key.strip() if isinstance(resource_key, str) else ""
    if not normalized_key:
        return None

    metadata = _resource_metadata_by_key().get(normalized_key)
    if metadata is None:
        return None

    icon_path = _resolve_repo_asset_path(_string_or_none(metadata.get("icon")))
    model_path = _resolve_resource_model_path(metadata.get("model"), is_water=is_water)
    model_size = _vector3(metadata.get("model_size"), default=(1.0, 1.0, 1.0))
    model_hpr = _vector3(metadata.get("model_hpr"), default=(0.0, 0.0, 0.0))
    model_offset = _vector3(metadata.get("model_position"), default=(0.0, 0.0, 0.10))

    return AssetPreviewInfo(
        kind="resource",
        key=normalized_key,
        display_name=resource_display_text(normalized_key) or normalized_key,
        source_class=str(metadata.get("source_class", normalized_key)),
        primary_image_label="Icon",
        primary_image_path=icon_path,
        primary_image_variants=(icon_path,) if icon_path is not None else (),
        model_path=model_path,
        model_scale=model_size,
        model_hpr=model_hpr,
        model_offset=model_offset,
    )


def render_model_preview_image(preview: AssetPreviewInfo) -> Path | None:
    if preview.model_path is None or not preview.model_path.exists() or not _PANDA3D_AVAILABLE:
        return None

    renderer = _get_model_preview_renderer()
    if renderer is None:
        return None

    cache_key = _model_preview_cache_key(preview)
    output_path = _MODEL_PREVIEW_CACHE_DIR / f"{cache_key}.png"
    if output_path.exists():
        return output_path

    try:
        rendered = renderer.render_preview(
            preview.model_path,
            scale=preview.model_scale,
            hpr=preview.model_hpr,
            offset=preview.model_offset,
            output_path=output_path,
        )
    except Exception:
        return None

    return output_path if rendered else None


@lru_cache(maxsize=1)
def _get_model_preview_renderer() -> _ModelPreviewRenderer | None:
    if not _PANDA3D_AVAILABLE:
        return None

    try:
        return _ModelPreviewRenderer()
    except Exception:
        return None


@lru_cache(maxsize=1)
def _terrain_previews_by_key() -> dict[str, AssetPreviewInfo]:
    previews: dict[str, AssetPreviewInfo] = {}

    for terrain_name, class_path in _OFFLINE_RESOURCE_TERRAIN_CLASS_PATHS.items():
        module_path, class_name = class_path.rsplit(".", 1)
        metadata = _parse_class_metadata(
            _module_file_from_module_path(module_path),
            class_name,
            class_defaults={
                "_model": None,
                "model_scale": (1.73, 1.73, 1.73),
                "model_hpr": (0.0, 0.0, 0.0),
                "model_pos_z_offset": -0.05,
                "_texture": None,
            },
            init_attribute_names={"_texture"},
        )
        if metadata is None:
            continue

        normalized_key = _normalize_identifier(terrain_name)
        if normalized_key is None:
            continue

        texture_path, texture_variants = _resolve_terrain_texture_paths(_string_or_none(metadata.get("_texture")))
        model_path = _resolve_model_path(_string_or_none(metadata.get("_model")))
        base_hpr = _vector3(metadata.get("model_hpr"), default=(0.0, 0.0, 0.0))
        model_hpr = (base_hpr[0] + 30.0, base_hpr[1], base_hpr[2])
        model_offset = (0.0, 0.0, _float_value(metadata.get("model_pos_z_offset"), default=-0.05))

        previews[normalized_key] = AssetPreviewInfo(
            kind="terrain",
            key=normalized_key,
            display_name=terrain_display_name(normalized_key) or terrain_name,
            source_class=class_path,
            primary_image_label="Texture",
            primary_image_path=texture_path,
            primary_image_variants=texture_variants,
            model_path=model_path,
            model_scale=_vector3(metadata.get("model_scale"), default=(1.73, 1.73, 1.73)),
            model_hpr=model_hpr,
            model_offset=model_offset,
        )

    return previews


@lru_cache(maxsize=1)
def _resource_metadata_by_key() -> dict[str, dict[str, object]]:
    metadata_by_key: dict[str, dict[str, object]] = {}

    for path in _RESOURCE_ROOT.rglob("*.py"):
        if path.name.startswith("__"):
            continue

        module = _parse_module(path)
        if module is None:
            continue

        module_name = _module_name_from_path(path)
        for class_def in (node for node in module.body if isinstance(node, ast.ClassDef)):
            metadata = _extract_class_metadata_from_def(
                class_def,
                class_defaults={
                    "key": None,
                    "icon": None,
                    "model": None,
                    "model_size": 1.0,
                    "model_position": (0.0, 0.0, 0.10),
                    "model_hpr": (0.0, 0.0, 0.0),
                },
                init_attribute_names=set(),
            )
            key = _string_or_none(metadata.get("key"))
            if key is None:
                continue

            metadata["source_class"] = f"{module_name}.{class_def.name}"
            metadata_by_key[key] = metadata

    return metadata_by_key


def _module_file_from_module_path(module_path: str) -> Path:
    return SCIV_ROOT / Path(*module_path.split(".")).with_suffix(".py")


def _module_name_from_path(path: Path) -> str:
    return ".".join(path.relative_to(SCIV_ROOT).with_suffix("").parts)


def _parse_class_metadata(
    path: Path,
    class_name: str,
    *,
    class_defaults: dict[str, object],
    init_attribute_names: set[str],
) -> dict[str, object] | None:
    module = _parse_module(path)
    if module is None:
        return None

    for class_def in (node for node in module.body if isinstance(node, ast.ClassDef)):
        if class_def.name == class_name:
            return _extract_class_metadata_from_def(
                class_def,
                class_defaults=class_defaults,
                init_attribute_names=init_attribute_names,
            )

    return None


def _parse_module(path: Path) -> ast.Module | None:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return None

    try:
        return ast.parse(source, filename=str(path))
    except SyntaxError:
        return None


def _extract_class_metadata_from_def(
    class_def: ast.ClassDef,
    *,
    class_defaults: dict[str, object],
    init_attribute_names: set[str],
) -> dict[str, object]:
    metadata = dict(class_defaults)

    for item in class_def.body:
        target_name = _assignment_target_name(item)
        if target_name is not None and target_name in metadata:
            value = _literal_value(_assignment_value(item))
            if value is not _UNSET:
                metadata[target_name] = value
            continue

        if isinstance(item, ast.FunctionDef) and item.name == "__init__" and init_attribute_names:
            for nested in ast.walk(item):
                if not isinstance(nested, ast.Assign):
                    continue
                for target in nested.targets:
                    attr_name = _self_attribute_name(target)
                    if attr_name is None or attr_name not in init_attribute_names:
                        continue
                    value = _literal_value(nested.value)
                    if value is not _UNSET:
                        metadata[attr_name] = value

    return metadata


def _assignment_target_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        return target.id if isinstance(target, ast.Name) else None
    if isinstance(node, ast.AnnAssign):
        target = node.target
        return target.id if isinstance(target, ast.Name) else None
    return None


def _assignment_value(node: ast.AST) -> ast.AST:
    if isinstance(node, ast.Assign):
        return node.value
    if isinstance(node, ast.AnnAssign):
        return node.value if node.value is not None else ast.Constant(value=None)
    raise TypeError(f"Unsupported assignment node: {type(node)!r}")


def _self_attribute_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        return node.attr
    return None


def _literal_value(node: ast.AST) -> object:
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Tuple | ast.List):
        values: list[object] = []
        for element in node.elts:
            parsed = _literal_value(element)
            if parsed is _UNSET:
                return _UNSET
            values.append(parsed)
        return tuple(values)

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        operand = _literal_value(node.operand)
        if isinstance(operand, int | float):
            return -operand

    return _UNSET


def _model_preview_cache_key(preview: AssetPreviewInfo) -> str:
    model_path = preview.model_path
    if model_path is None:
        return "missing"

    digest_input = "|".join(
        (
            str(model_path.resolve()),
            str(model_path.stat().st_mtime_ns),
            repr(preview.model_scale),
            repr(preview.model_hpr),
            repr(preview.model_offset),
        )
    )
    return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()


def _normalize_identifier(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().replace("_", "").replace("-", "").lower()
    return normalized or None


def _resolve_repo_asset_path(asset_path: str | None) -> Path | None:
    if asset_path is None:
        return None

    raw_value = asset_path.strip()
    if not raw_value:
        return None

    candidate = Path(raw_value).expanduser()
    if candidate.is_absolute():
        return candidate

    repo_candidate = REPO_ROOT / raw_value
    if repo_candidate.exists():
        return repo_candidate

    sciv_candidate = SCIV_ROOT / raw_value
    if sciv_candidate.exists():
        return sciv_candidate

    return repo_candidate


def _resolve_model_path(model_value: str | None) -> Path | None:
    path = _resolve_repo_asset_path(model_value)
    if path is None:
        return None
    return path if path.exists() else None


def _resolve_resource_model_path(model_value: object, *, is_water: bool) -> Path | None:
    if isinstance(model_value, str):
        return _resolve_model_path(model_value)

    if isinstance(model_value, tuple) and len(model_value) == 2:
        land_model, water_model = model_value
        selected = water_model if is_water else land_model
        return _resolve_model_path(_string_or_none(selected))

    return None


def _resolve_terrain_texture_paths(texture_value: str | None) -> tuple[Path | None, tuple[Path, ...]]:
    direct_path = _resolve_repo_asset_path(texture_value)
    if direct_path is not None and direct_path.exists():
        return direct_path, (direct_path,)

    if texture_value is None:
        return None, ()

    filename = Path(texture_value).name
    matches = tuple(path for root in _TERRAIN_TEXTURE_ROOTS if (path := root / filename).exists())
    if matches:
        return matches[0], matches

    return None, ()


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _float_value(value: object, *, default: float) -> float:
    if isinstance(value, int | float):
        return float(value)
    return default


def _vector3(value: object, *, default: PreviewVector) -> PreviewVector:
    if isinstance(value, tuple | list) and len(value) == 3:
        first, second, third = value
        if isinstance(first, int | float) and isinstance(second, int | float) and isinstance(third, int | float):
            return float(first), float(second), float(third)

    if isinstance(value, int | float):
        scalar = float(value)
        return scalar, scalar, scalar

    return default

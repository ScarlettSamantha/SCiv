"""Application entry and main window for the standalone SCiv worldgen viewer."""

import argparse
import multiprocessing
import os
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PyQt6.QtCore import QObject, QPointF, QSize, QThread, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor, QFont, QFontDatabase, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QSplitter,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from worldgen_asset_preview_support import (
    AssetPreviewInfo,
    format_asset_preview_metadata,
    preview_path_text,
    render_model_preview_image,
    resolve_resource_asset_preview,
    resolve_terrain_asset_preview,
)
from worldgen_generation_support import (
    OfflineGeneratorSpec,
    generate_random_seed,
    generate_world_payload,
    list_offline_generators,
    resolve_offline_generator,
)
from worldgen_viewer_tool.geometry import _hex_center, _hex_polygon, _neighbor_coord_for_side, _river_line, _river_segment_key
from worldgen_viewer_tool.palette import (
    BIOME_COLORS,
    GEOFORM_COLORS,
    LABEL_COLORS,
    MAX_OVERLAY_SUMMARY_ITEMS,
    MAX_RESOURCE_LEGEND_ITEMS,
    MAX_TERRITORY_LEGEND_ITEMS,
    OVERLAY_BUCKET_ORDER,
    RIVER_COLORS,
    _altitude_bucket_label,
    _altitude_color,
    _heightmap_sealevel,
    _moisture_bucket_label,
    _moisture_color,
    _overlay_water_label,
    _resource_color,
    _resource_label,
    _runtime_resource_key,
    _runtime_terrain_color,
    _runtime_terrain_key,
    _runtime_terrain_label,
    _stable_color,
    _title_from_identifier,
    _water_color_for_record,
)
from worldgen_viewer_tool.widgets.legend import LegendEntrySpec, LegendEntryWidget
from worldgen_viewer_support import (
    HexCoord,
    HexRecord,
    ManifestEntry,
    WorldgenDump,
    format_dump_summary,
    format_hex_details,
    format_hex_tooltip,
    load_manifest,
    load_worldgen_dump,
    load_worldgen_payload,
    river_role_label as river_role_label_for_record,
)


MAX_PREVIEW_SEED = 2**31 - 1
MAX_PREVIEW_MAP_DIMENSION = 500
PREVIEW_GENERATION_STEPS = 6
OVERVIEW_CARD_COLUMNS = 3
OVERVIEW_CARD_MIN_WIDTH = 170
OVERVIEW_THUMBNAIL_WIDTH = 220
OVERVIEW_THUMBNAIL_HEIGHT = 150
MAX_PARALLEL_PREVIEW_WORKERS = 6


@dataclass(frozen=True, slots=True)
class PreviewGenerationRequest:
    generator_spec: OfflineGeneratorSpec
    width: int
    height: int
    seeds: tuple[int, ...]
    options: dict[str, str]


@dataclass(frozen=True, slots=True)
class GeneratedPreviewResult:
    dump: WorldgenDump
    source_label: str
    seed: int


@dataclass(frozen=True, slots=True)
class GeneratedPreviewPayloadResult:
    payload: dict[str, object]
    source_label: str
    seed: int
    batch_index: int


def _preview_process_context() -> multiprocessing.context.BaseContext:
    if sys.platform == "win32":
        return multiprocessing.get_context("spawn")

    available_methods = set(multiprocessing.get_all_start_methods())
    if "forkserver" in available_methods:
        return multiprocessing.get_context("forkserver")

    return multiprocessing.get_context("spawn")


def _generate_preview_payload_result(
    batch_index: int,
    batch_size: int,
    generator_spec: OfflineGeneratorSpec,
    width: int,
    height: int,
    seed: int,
    options: dict[str, str],
) -> GeneratedPreviewPayloadResult:
    payload = generate_world_payload(
        generator_spec,
        width=width,
        height=height,
        seed=seed,
        options=options,
        debug=False,
        source="viewer",
        extra_meta={
            "viewer_preview": {
                "generated_in_viewer": True,
                "batch_size": batch_size,
                "batch_index": batch_index,
            }
        },
    )
    source_label = _build_generated_label_text(
        generator_spec,
        width,
        height,
        seed,
        options,
    )
    return GeneratedPreviewPayloadResult(
        payload=payload,
        source_label=source_label,
        seed=seed,
        batch_index=batch_index,
    )


class PreviewGenerationWorker(QObject):
    progress_changed = pyqtSignal(int, int, str)
    generation_succeeded = pyqtSignal(object)
    generation_failed = pyqtSignal(str)

    def __init__(self, request: PreviewGenerationRequest) -> None:
        super().__init__()
        self.request = request

    def run(self) -> None:
        try:
            if len(self.request.seeds) <= 1:
                generated_results = [self._run_single_preview_generation()]
            else:
                generated_results = self._run_parallel_batch_generation()
        except Exception as exc:  # noqa: BLE001
            self.generation_failed.emit(str(exc))
            return

        self.generation_succeeded.emit(tuple(generated_results))

    def _run_single_preview_generation(self) -> GeneratedPreviewResult:
        seed = self.request.seeds[0]
        payload = generate_world_payload(
            self.request.generator_spec,
            width=self.request.width,
            height=self.request.height,
            seed=seed,
            options=self.request.options,
            debug=False,
            source="viewer",
            extra_meta={
                "viewer_preview": {
                    "generated_in_viewer": True,
                    "batch_size": 1,
                    "batch_index": 1,
                }
            },
            progress_callback=lambda step, total, message: self._emit_generation_progress(1, 1, step, total, message),
        )
        self.progress_changed.emit(PREVIEW_GENERATION_STEPS, PREVIEW_GENERATION_STEPS, "Loading preview dump")
        return self._load_generated_result(
            GeneratedPreviewPayloadResult(
                payload=payload,
                source_label=_build_generated_label_text(
                    self.request.generator_spec,
                    self.request.width,
                    self.request.height,
                    seed,
                    self.request.options,
                ),
                seed=seed,
                batch_index=1,
            )
        )

    def _run_parallel_batch_generation(self) -> list[GeneratedPreviewResult]:
        world_count = len(self.request.seeds)
        worker_count = min(world_count, max(1, os.cpu_count() or 1), MAX_PARALLEL_PREVIEW_WORKERS)
        self.progress_changed.emit(0, world_count, f"Generating {world_count} worlds using {worker_count} processes")

        payload_results_by_index: dict[int, GeneratedPreviewPayloadResult] = {}
        with ProcessPoolExecutor(max_workers=worker_count, mp_context=_preview_process_context()) as executor:
            future_to_batch_index = {
                executor.submit(
                    _generate_preview_payload_result,
                    batch_index,
                    world_count,
                    self.request.generator_spec,
                    self.request.width,
                    self.request.height,
                    seed,
                    self.request.options,
                ): batch_index
                for batch_index, seed in enumerate(self.request.seeds, start=1)
            }

            completed = 0
            for future in as_completed(future_to_batch_index):
                payload_result = future.result()
                payload_results_by_index[payload_result.batch_index] = payload_result
                completed += 1
                self.progress_changed.emit(
                    completed,
                    world_count,
                    f"Completed {completed}/{world_count} worlds — latest seed {payload_result.seed}",
                )

        self.progress_changed.emit(world_count, world_count, "Loading generated worlds")
        return [
            self._load_generated_result(payload_results_by_index[batch_index])
            for batch_index in sorted(payload_results_by_index)
        ]

    def _load_generated_result(self, payload_result: GeneratedPreviewPayloadResult) -> GeneratedPreviewResult:
        dump = load_worldgen_payload(payload_result.payload, path=Path("<generated>"))
        return GeneratedPreviewResult(
            dump=dump,
            source_label=payload_result.source_label,
            seed=payload_result.seed,
        )

    def _emit_generation_progress(
        self,
        world_index: int,
        world_count: int,
        step: int,
        total: int,
        message: str,
    ) -> None:
        del total
        absolute_step = (world_index - 1) * PREVIEW_GENERATION_STEPS + step
        self.progress_changed.emit(
            absolute_step,
            world_count * PREVIEW_GENERATION_STEPS,
            self._progress_message(world_index, world_count, message),
        )

    def _progress_message(self, world_index: int, world_count: int, message: str) -> str:
        if world_count <= 1:
            return message
        return f"World {world_index}/{world_count} — {message}"


def _build_generated_label_text(
    generator_spec: OfflineGeneratorSpec,
    width: int,
    height: int,
    seed: int,
    options: dict[str, str],
) -> str:
    option_labels = {option.key: option.label for option in generator_spec.options}
    parts = [
        f"Generated preview: {generator_spec.name}",
        f"Size: {width} × {height}",
        f"Seed: {seed}",
    ]
    if options:
        rendered_options = ", ".join(f"{option_labels.get(key, key)}={value}" for key, value in options.items())
        parts.append(f"Options: {rendered_options}")
    return "\n".join(parts)


class HexItem(QGraphicsPolygonItem):
    def __init__(self, coord: HexCoord, on_selected: Callable[[HexCoord], None]) -> None:
        super().__init__()
        self.coord = coord
        self._on_selected = on_selected

    def mousePressEvent(self, event) -> None:  # noqa: ANN001
        self._on_selected(self.coord)
        super().mousePressEvent(event)


class PreviewSurfaceWidget(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self._pixmap: QPixmap | None = None

        self.setObjectName("preview-surface")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(
            "QFrame#preview-surface {"
            "background-color: rgba(255, 255, 255, 0.02);"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 8px;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: 600;")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(190)
        self.image_label.setWordWrap(True)
        self.image_label.setStyleSheet(
            "background-color: #17191f;"
            "border: 1px solid #2c313a;"
            "border-radius: 6px;"
            "padding: 8px;"
        )

        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.path_label.setStyleSheet("color: #b9c0ca;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.image_label)
        layout.addWidget(self.path_label)

    def set_surface(self, *, title: str, pixmap: QPixmap | None, empty_text: str, path_text: str | None) -> None:
        self.title_label.setText(title)
        self._pixmap = pixmap

        if pixmap is None:
            self.image_label.clear()
            self.image_label.setText(empty_text)
            if path_text is None:
                self.path_label.setText("")
            else:
                self.path_label.setText(f"{path_text}\n{empty_text}")
            return

        self.image_label.setText("")
        self._apply_pixmap()
        self.path_label.setText(path_text or "")

    def resizeEvent(self, event) -> None:  # noqa: ANN001
        self._apply_pixmap()
        super().resizeEvent(event)

    def _apply_pixmap(self) -> None:
        if self._pixmap is None:
            return

        target_size = self.image_label.contentsRect().size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            return

        scaled = self._pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)


class AssetPreviewGroupWidget(QGroupBox):
    def __init__(self, title: str, empty_message: str) -> None:
        super().__init__(title)
        self._base_title = title
        self._empty_message = empty_message

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.primary_surface = PreviewSurfaceWidget("Texture")
        self.model_surface = PreviewSurfaceWidget("Model")

        self.meta_label = QLabel()
        self.meta_label.setWordWrap(True)
        self.meta_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.meta_label.setStyleSheet("color: #c4ccd7;")

        layout.addWidget(self.summary_label)
        layout.addWidget(self.primary_surface)
        layout.addWidget(self.model_surface)
        layout.addWidget(self.meta_label)

        self.clear()

    def clear(self, message: str | None = None) -> None:
        self.setTitle(self._base_title)
        self.summary_label.setText(message or self._empty_message)
        self.primary_surface.hide()
        self.model_surface.hide()
        self.meta_label.hide()
        self.meta_label.setText("")

    def set_preview(
        self,
        preview: AssetPreviewInfo,
        *,
        primary_pixmap: QPixmap | None,
        model_pixmap: QPixmap | None,
    ) -> None:
        self.setTitle(f"{self._base_title} — {preview.display_name}")
        self.summary_label.setText(f"{preview.display_name} · {preview.key}")

        primary_path_text = preview_path_text(preview.primary_image_path)
        primary_empty_text = f"No {preview.primary_image_label.lower()} image was found for this asset."
        self.primary_surface.set_surface(
            title=preview.primary_image_label,
            pixmap=primary_pixmap,
            empty_text=primary_empty_text,
            path_text=primary_path_text,
        )
        self.primary_surface.show()

        model_path_text = preview_path_text(preview.model_path)
        if preview.model_path is None:
            model_empty_text = "No model asset is defined for this item."
        else:
            model_empty_text = "Model preview could not be rendered in the standalone viewer."
        self.model_surface.set_surface(
            title="Model",
            pixmap=model_pixmap,
            empty_text=model_empty_text,
            path_text=model_path_text,
        )
        self.model_surface.show()

        self.meta_label.setText(format_asset_preview_metadata(preview))
        self.meta_label.show()


class MapView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene) -> None:
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setBackgroundBrush(QBrush(QColor("#1d1f24")))

    def wheelEvent(self, event) -> None:  # noqa: ANN001
        zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(zoom_factor, zoom_factor)


class GeneratedOverviewScrollArea(QScrollArea):
    resized = pyqtSignal()

    def resizeEvent(self, event) -> None:  # noqa: ANN001
        super().resizeEvent(event)
        self.resized.emit()


class WorldgenViewerWindow(QMainWindow):
    def __init__(self, initial_path: Path | None = None) -> None:
        super().__init__()
        self.setWindowTitle("SCiv Worldgen Viewer")
        self.resize(1500, 960)
        self.setAcceptDrops(True)

        self.dump: WorldgenDump | None = None
        self.selected_coord: HexCoord | None = None
        self.current_manifest_path: Path | None = None
        self.manifest_entries: tuple[ManifestEntry, ...] = ()
        self.generated_preview_results: tuple[GeneratedPreviewResult, ...] = ()
        self.selected_generated_preview_index: int | None = None
        self.generated_overview_buttons: list[QToolButton] = []
        self.hex_items: dict[HexCoord, HexItem] = {}
        self.river_glow_items: list[QGraphicsLineItem] = []
        self.river_items: list[QGraphicsLineItem] = []
        self.legend_entry_widgets: list[LegendEntryWidget] = []
        self.sidebar_sections: dict[str, QWidget] = {}
        self.sidebar_section_actions: dict[str, QAction] = {}
        self.label_items: dict[str, list[QGraphicsSimpleTextItem]] = {
            "landmasses": [],
            "biome_regions": [],
            "rivers": [],
            "territories": [],
        }
        self.hovered_legend_label: str | None = None
        self.generation_thread: QThread | None = None
        self.generation_worker: PreviewGenerationWorker | None = None

        self.scene = QGraphicsScene(self)
        self.view = MapView(self.scene)
        self.info_panel = QPlainTextEdit()
        self.info_panel.setReadOnly(True)
        self.overlay_summary_panel = QPlainTextEdit()
        self.overlay_summary_panel.setReadOnly(True)
        self.overlay_summary_panel.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.overlay_summary_panel.setMinimumHeight(210)
        self.overlay_summary_panel.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))

        self.file_label = QLabel("Open a world dump or batch manifest to get started.")
        self.file_label.setWordWrap(True)
        self.summary_label = QLabel("No world loaded yet.")
        self.summary_label.setWordWrap(True)

        self.generation_error: str | None = None
        try:
            self.generator_specs = list_offline_generators()
        except Exception as exc:  # noqa: BLE001
            self.generator_specs = ()
            self.generation_error = str(exc)
        self.generation_option_controls: dict[str, tuple[QLabel, QComboBox]] = {}
        self.legend_group = self._build_legend_group()
        self.preview_pixmaps_by_path: dict[Path, QPixmap | None] = {}
        self.terrain_preview_group = AssetPreviewGroupWidget(
            "Terrain asset",
            "Select a hex to preview its terrain texture and model.",
        )
        self.resource_preview_group = AssetPreviewGroupWidget(
            "Resource asset",
            "Select a hex to preview its resource icon and model.",
        )
        self.generated_preview_selector = QComboBox()
        self.generated_preview_selector.currentIndexChanged.connect(self._on_generated_preview_selector_changed)
        self.generated_preview_overview_button = QPushButton("Overview")
        self.generated_preview_overview_button.clicked.connect(self._show_generated_overview)
        self.generated_preview_overview_button.setEnabled(False)

        self.manifest_selector = QComboBox()
        self.manifest_selector.currentIndexChanged.connect(self._load_manifest_entry)
        self.manifest_selector.hide()

        self.generator_combo = QComboBox()
        for spec in self.generator_specs:
            self.generator_combo.addItem(spec.name, spec.name)
        self.generator_combo.currentIndexChanged.connect(self._sync_generation_option_controls)

        self.generate_width_spin = QSpinBox()
        self.generate_width_spin.setRange(1, MAX_PREVIEW_MAP_DIMENSION)
        self.generate_width_spin.setValue(50)

        self.generate_height_spin = QSpinBox()
        self.generate_height_spin.setRange(1, MAX_PREVIEW_MAP_DIMENSION)
        self.generate_height_spin.setValue(50)

        self.generate_seed_spin = QSpinBox()
        self.generate_seed_spin.setRange(0, MAX_PREVIEW_SEED)
        self.generate_seed_spin.setSpecialValueText("Random")
        self.generate_seed_spin.setValue(0)

        self.generate_count_spin = QSpinBox()
        self.generate_count_spin.setRange(1, 24)
        self.generate_count_spin.setValue(1)
        self.generate_count_spin.valueChanged.connect(self._update_generation_button_text)

        self.randomize_seed_button = QPushButton("Random")
        self.randomize_seed_button.clicked.connect(self._randomize_seed)

        self.generator_options_note = QLabel()
        self.generator_options_note.setWordWrap(True)

        self.generation_option_form = QFormLayout()
        for spec in self.generator_specs:
            for option in spec.options:
                if option.key in self.generation_option_controls:
                    continue
                label = QLabel(option.label)
                combo = QComboBox()
                combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
                self.generation_option_form.addRow(label, combo)
                self.generation_option_controls[option.key] = (label, combo)

        self.generate_button = QPushButton("Generate preview")
        self.generate_button.clicked.connect(self._generate_preview)

        self.generation_progress_label = QLabel("")
        self.generation_progress_label.setWordWrap(True)
        self.generation_progress_label.hide()

        self.generation_progress_bar = QProgressBar()
        self.generation_progress_bar.setTextVisible(True)
        self.generation_progress_bar.setFormat("%v/%m")
        self.generation_progress_bar.hide()

        self.generated_overview_page = self._build_generated_overview_page()
        self.center_stack = QStackedWidget()
        self.center_stack.addWidget(self.view)
        self.center_stack.addWidget(self.generated_overview_page)
        self.center_stack.setCurrentWidget(self.view)

        self.base_layer_combo = QComboBox()
        self.base_layer_combo.addItem("Biome", "biome")
        self.base_layer_combo.addItem("Altitude", "altitude")
        self.base_layer_combo.addItem("Moisture", "moisture")
        self.base_layer_combo.addItem("Geoform", "geoform")
        self.base_layer_combo.addItem("Territory", "territory")
        self.base_layer_combo.addItem("Rivers", "rivers")
        self.base_layer_combo.addItem("Runtime Terrain", "runtime-terrain")
        self.base_layer_combo.addItem("Resources", "resources")
        self.base_layer_combo.addItem("Visibility", "visibility")
        self.base_layer_combo.currentIndexChanged.connect(self._on_base_layer_changed)

        self.overlay_scope_combo = QComboBox()
        self.overlay_scope_combo.addItem("Visible runtime area", "runtime-visible")
        self.overlay_scope_combo.addItem("Entire raw dump", "all")
        self.overlay_scope_combo.currentIndexChanged.connect(self._update_overlay_summary)

        self.show_grid_checkbox = QCheckBox("Show hex grid")
        self.show_grid_checkbox.setChecked(True)
        self.show_grid_checkbox.toggled.connect(self._apply_visuals)

        self.show_rivers_checkbox = QCheckBox("Show river edges")
        self.show_rivers_checkbox.setChecked(True)
        self.show_rivers_checkbox.toggled.connect(self._apply_visuals)

        self.show_landmass_labels_checkbox = QCheckBox("Show landmass names")
        self.show_landmass_labels_checkbox.setChecked(True)
        self.show_landmass_labels_checkbox.toggled.connect(self._apply_visuals)

        self.show_biome_labels_checkbox = QCheckBox("Show biome region names")
        self.show_biome_labels_checkbox.setChecked(False)
        self.show_biome_labels_checkbox.toggled.connect(self._apply_visuals)

        self.show_river_labels_checkbox = QCheckBox("Show river names")
        self.show_river_labels_checkbox.setChecked(False)
        self.show_river_labels_checkbox.toggled.connect(self._apply_visuals)

        self.dim_hidden_checkbox = QCheckBox("Dim tiles outside runtime bounds")
        self.dim_hidden_checkbox.setChecked(True)
        self.dim_hidden_checkbox.toggled.connect(self._apply_visuals)

        open_button = QPushButton("Open dump…")
        open_button.clicked.connect(self._open_file_dialog)
        fit_button = QPushButton("Fit to view")
        fit_button.clicked.connect(self._fit_scene)

        self.coord_col_spin = QSpinBox()
        self.coord_col_spin.setRange(0, 0)

        self.coord_row_spin = QSpinBox()
        self.coord_row_spin.setRange(0, 0)

        self.jump_button = QPushButton("Jump to coord")
        self.jump_button.clicked.connect(self._jump_to_coord)

        self.center_selected_button = QPushButton("Center selected")
        self.center_selected_button.clicked.connect(self._center_on_selected_hex)

        self.clear_selection_button = QPushButton("Clear selection")
        self.clear_selection_button.clicked.connect(self._clear_selection)

        self.copy_details_button = QPushButton("Copy details")
        self.copy_details_button.clicked.connect(self._copy_current_details)

        controls_panel = self._build_controls_panel(open_button, fit_button)
        details_panel = self._build_details_panel()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(controls_panel)
        splitter.addWidget(self.center_stack)
        splitter.addWidget(details_panel)
        splitter.setSizes([340, 820, 340])

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        self.setCentralWidget(container)

        self._setup_menu()
        self.statusBar().showMessage("Ready")
        self._sync_manifest_selector()
        self._sync_generation_option_controls()
        self._update_legend()
        self._update_overlay_summary()
        self._update_info_panel()
        self._update_asset_preview_panels()
        self._update_selection_controls()
        self._update_generation_button_text()
        self._update_generated_overview_navigation_action()

        if initial_path is not None:
            self.load_input_path(initial_path)

    def dragEnterEvent(self, event) -> None:  # noqa: ANN001
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: ANN001
        urls = event.mimeData().urls()
        if not urls:
            return

        file_path = Path(urls[0].toLocalFile())
        if file_path.exists():
            self.load_input_path(file_path)
            event.acceptProposedAction()

    def closeEvent(self, event) -> None:  # noqa: ANN001
        if self.generation_thread is not None and self.generation_thread.isRunning():
            QMessageBox.information(
                self,
                "Generation in progress",
                "Please wait for the current preview generation to finish before closing the viewer.",
            )
            event.ignore()
            return

        super().closeEvent(event)

    def load_input_path(self, path: Path) -> None:
        try:
            manifest_entries = load_manifest(path)
            if manifest_entries is not None:
                if not manifest_entries:
                    raise ValueError(f"No world files were found in {path}.")
                self._clear_generated_previews()
                self.current_manifest_path = path
                self.manifest_entries = manifest_entries
                self._sync_manifest_selector()
                self.manifest_selector.blockSignals(True)
                self.manifest_selector.setCurrentIndex(0)
                self.manifest_selector.blockSignals(False)
                self._load_manifest_entry(0)
                return

            self.current_manifest_path = None
            self.manifest_entries = ()
            self._sync_manifest_selector()
            self._load_dump(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Unable to load file", str(exc))
            self.statusBar().showMessage(f"Load failed: {exc}")

    def _load_dump(self, path: Path) -> None:
        dump = load_worldgen_dump(path)
        self._clear_generated_previews()
        self._apply_loaded_dump(dump, self._format_loaded_file_label(dump.path))

    def _load_dump_payload(self, payload: dict[str, object], source_label: str) -> None:
        dump = load_worldgen_payload(payload, path=Path("<generated>"))
        self._clear_generated_previews()
        self._apply_loaded_dump(dump, source_label)

    def _apply_loaded_dump(self, dump: WorldgenDump, source_label: str) -> None:
        self.dump = dump
        self.selected_coord = None
        self.file_label.setText(source_label)
        self.summary_label.setText(format_dump_summary(dump))
        self._update_coordinate_ranges()
        self._sync_coordinate_inputs()
        self._rebuild_scene()
        self._update_legend()
        self._update_overlay_summary()
        self._update_info_panel()
        self._update_asset_preview_panels()
        self._update_selection_controls()
        self.statusBar().showMessage(f"Loaded {dump.title} with {len(dump.hexes)} hexes")

    def _load_manifest_entry(self, index: int) -> None:
        if index < 0 or index >= len(self.manifest_entries):
            return
        self._load_dump(self.manifest_entries[index].file_path)

    def _rebuild_scene(self) -> None:
        self.scene.clear()
        self.hex_items.clear()
        self.river_glow_items.clear()
        self.river_items.clear()
        for label_group in self.label_items.values():
            label_group.clear()

        if self.dump is None:
            return

        river_keys: set[tuple[tuple[int, int], tuple[int, int]] | tuple[HexCoord, str]] = set()
        label_font = QFont()
        label_font.setPointSize(10)
        label_font.setBold(True)

        for record in self.dump.hexes:
            polygon = QPolygonF([QPointF(point.x(), point.y()) for point in _hex_polygon(record.coord)])
            item = HexItem(record.coord, self._select_hex)
            item.setPolygon(polygon)
            item.setToolTip(format_hex_tooltip(self.dump, record.coord))
            item.setZValue(1)
            self.scene.addItem(item)
            self.hex_items[record.coord] = item

            for river_segment in record.river_segments:
                edge = river_segment.get("edge") if isinstance(river_segment.get("edge"), dict) else {}
                side_value = river_segment.get("side")
                side = str(side_value) if isinstance(side_value, str) and side_value else str(edge.get("side", ""))
                if _neighbor_coord_for_side(record.coord, side) is None:
                    continue

                river_key = _river_segment_key(record.coord, edge, side)
                if river_key in river_keys:
                    continue
                river_keys.add(river_key)

                start_point, end_point = _river_line(record.coord, side)
                glow_item = QGraphicsLineItem(start_point.x(), start_point.y(), end_point.x(), end_point.y())
                glow_item.setZValue(19)
                self.scene.addItem(glow_item)
                self.river_glow_items.append(glow_item)

                river_item = QGraphicsLineItem(start_point.x(), start_point.y(), end_point.x(), end_point.y())
                river_item.setZValue(20)
                self.scene.addItem(river_item)
                self.river_items.append(river_item)

        for kind, regions in self.dump.named_regions.items():
            for region in regions:
                if region.anchor is None:
                    continue
                anchor = _hex_center(region.anchor)
                label_item = QGraphicsSimpleTextItem(region.name)
                label_item.setFont(label_font)
                label_item.setBrush(QBrush(LABEL_COLORS.get(kind, QColor("#f1f1f1"))))
                bounds = label_item.boundingRect()
                label_item.setPos(anchor.x() - bounds.width() / 2, anchor.y() - bounds.height() / 2)
                label_item.setZValue(40)
                self.scene.addItem(label_item)
                self.label_items.setdefault(kind, []).append(label_item)

        self._apply_visuals()
        self._fit_scene()

    def _on_base_layer_changed(self) -> None:
        self._apply_visuals()
        self._update_legend()
        self._update_overlay_summary()

    def _apply_visuals(self) -> None:
        if self.dump is None:
            return

        grid_pen = QPen(QColor(0, 0, 0, 160), 0.8)
        hidden_pen = QPen(QColor(0, 0, 0, 60), 0.6)
        selected_pen = QPen(QColor("#ff5f5f"), 2.2)
        legend_match_pen = QPen(QColor("#ffe082"), 2.0)
        no_pen = QPen()
        no_pen.setStyle(Qt.PenStyle.NoPen)
        active_mode = str(self.base_layer_combo.currentData())
        emphasize_rivers = active_mode == "rivers"

        for coord, item in self.hex_items.items():
            record = self.dump.hexes_by_coord[coord]
            color = self._color_for_hex(record)
            matches_hover = self.hovered_legend_label is None or self._overlay_bucket_label(record, active_mode) == self.hovered_legend_label
            if self.dim_hidden_checkbox.isChecked() and not record.visible_in_runtime:
                color = QColor(color)
                color.setAlpha(95)
            if self.hovered_legend_label is not None and not matches_hover:
                color = QColor(color)
                color.setAlpha(min(color.alpha(), 46))

            item.setBrush(QBrush(color))
            if coord == self.selected_coord:
                item.setPen(selected_pen)
            elif self.hovered_legend_label is not None and matches_hover:
                item.setPen(legend_match_pen)
            elif self.show_grid_checkbox.isChecked():
                item.setPen(grid_pen if record.visible_in_runtime else hidden_pen)
            else:
                item.setPen(no_pen)

        river_glow_pen = QPen(QColor(117, 219, 255, 120), 6.0 if emphasize_rivers else 4.2)
        river_glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        river_glow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        river_pen = QPen(QColor("#d7f4ff") if emphasize_rivers else QColor("#59b8ff"), 3.2 if emphasize_rivers else 2.5)
        river_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        river_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        show_river_overlay = self.show_rivers_checkbox.isChecked() or emphasize_rivers

        for glow_item in self.river_glow_items:
            glow_item.setVisible(show_river_overlay)
            glow_item.setPen(river_glow_pen)

        for river_item in self.river_items:
            river_item.setVisible(show_river_overlay)
            river_item.setPen(river_pen)

        for label_item in self.label_items.get("landmasses", []):
            label_item.setVisible(self.show_landmass_labels_checkbox.isChecked())
        for label_item in self.label_items.get("biome_regions", []):
            label_item.setVisible(self.show_biome_labels_checkbox.isChecked())
        for label_item in self.label_items.get("rivers", []):
            label_item.setVisible(self.show_river_labels_checkbox.isChecked())
        for label_item in self.label_items.get("territories", []):
            label_item.setVisible(active_mode == "territory")

    def _select_hex(self, coord: HexCoord) -> None:
        self.selected_coord = coord
        self._sync_coordinate_inputs(coord)
        self._apply_visuals()
        self._update_info_panel()
        self._update_asset_preview_panels()
        self._update_selection_controls()
        self.statusBar().showMessage(f"Selected hex {coord[0]}, {coord[1]}")

    def _update_info_panel(self) -> None:
        if self.dump is None:
            self.info_panel.setPlainText("Load a dump to inspect map data.")
            return

        if self.selected_coord is None:
            self.info_panel.setPlainText(format_dump_summary(self.dump))
            return

        self.info_panel.setPlainText(format_hex_details(self.dump, self.selected_coord))

    def _open_file_dialog(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open worldgen export",
            str(Path.cwd()),
            "Worldgen exports (*.json *.json.gz);;All files (*)",
        )
        if file_name:
            self.load_input_path(Path(file_name))

    def _fit_scene(self) -> None:
        if self.scene.items():
            self.view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _setup_menu(self) -> None:
        self.open_action = self._create_action(
            "Open…",
            self._open_file_dialog,
            status_tip="Open a world dump or batch manifest.",
        )
        self.fit_action = self._create_action(
            "Fit",
            self._fit_scene,
            status_tip="Fit the current map to the view.",
        )
        self.generate_action = self._create_action(
            "Generate",
            self._generate_preview,
            status_tip="Generate one or more previews with the current settings.",
        )
        self.randomize_seed_action = self._create_action(
            "Random seed",
            self._randomize_seed,
            status_tip="Choose a fresh random seed for preview generation.",
        )
        self.back_to_overview_action = self._create_action(
            "Back to overview",
            self._show_generated_overview,
            status_tip="Return to the generated-world overview grid.",
        )
        self.back_to_overview_action.setEnabled(False)
        self.center_selected_action = self._create_action(
            "Center",
            self._center_on_selected_hex,
            status_tip="Center the map on the selected hex.",
        )
        self.clear_selection_action = self._create_action(
            "Clear",
            self._clear_selection,
            status_tip="Clear the current hex selection.",
        )
        self.copy_details_action = self._create_action(
            "Copy details",
            self._copy_current_details,
            status_tip="Copy the current inspector text.",
        )
        self.quit_action = self._create_action(
            "Quit",
            self.close,
            status_tip="Close the viewer.",
        )

        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.quit_action)

        generate_menu = menu_bar.addMenu("&Generate")
        generate_menu.addAction(self.generate_action)
        generate_menu.addAction(self.randomize_seed_action)

        view_menu = menu_bar.addMenu("&View")
        view_menu.addAction(self.back_to_overview_action)
        view_menu.addSeparator()
        view_menu.addAction(self.fit_action)
        view_menu.addSeparator()

        map_menu = view_menu.addMenu("Map")
        self._add_checkbox_action(map_menu, "Grid", self.show_grid_checkbox)
        self._add_checkbox_action(map_menu, "Rivers", self.show_rivers_checkbox)
        self._add_checkbox_action(map_menu, "Dim outside bounds", self.dim_hidden_checkbox)

        labels_menu = view_menu.addMenu("Labels")
        self._add_checkbox_action(labels_menu, "Landmasses", self.show_landmass_labels_checkbox)
        self._add_checkbox_action(labels_menu, "Biomes", self.show_biome_labels_checkbox)
        self._add_checkbox_action(labels_menu, "River names", self.show_river_labels_checkbox)

        sidebar_menu = view_menu.addMenu("Sidebar")
        self._add_sidebar_section_action(sidebar_menu, "File", "file")
        self._add_sidebar_section_action(sidebar_menu, "Generate", "generation")
        self._add_sidebar_section_action(sidebar_menu, "Manifest", "manifest")
        self._add_sidebar_section_action(sidebar_menu, "Render", "render")
        self._add_sidebar_section_action(sidebar_menu, "Legend", "legend")
        self._add_sidebar_section_action(sidebar_menu, "Coverage", "overlay")
        self._add_sidebar_section_action(sidebar_menu, "Labels", "labels")
        self._add_sidebar_section_action(sidebar_menu, "Summary", "summary")

        inspect_menu = menu_bar.addMenu("&Inspect")
        inspect_menu.addAction(self.center_selected_action)
        inspect_menu.addAction(self.clear_selection_action)
        inspect_menu.addSeparator()
        inspect_menu.addAction(self.copy_details_action)

        toolbar = QToolBar("Worldgen", self)
        toolbar.setMovable(False)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.generate_action)
        toolbar.addAction(self.randomize_seed_action)
        toolbar.addAction(self.back_to_overview_action)
        toolbar.addAction(self.fit_action)
        toolbar.addSeparator()
        toolbar.addAction(self.center_selected_action)
        toolbar.addAction(self.clear_selection_action)
        toolbar.addAction(self.copy_details_action)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        self._apply_all_sidebar_section_visibility()

    def _create_action(
        self,
        title: str,
        handler: Callable[[], object],
        *,
        status_tip: str,
    ) -> QAction:
        action = QAction(title, self)
        action.triggered.connect(handler)
        action.setStatusTip(status_tip)
        action.setToolTip(status_tip)
        return action

    def _add_checkbox_action(self, menu, title: str, checkbox: QCheckBox) -> None:  # noqa: ANN001
        action = QAction(title, self)
        action.setCheckable(True)
        action.setChecked(checkbox.isChecked())
        action.toggled.connect(checkbox.setChecked)
        checkbox.toggled.connect(action.setChecked)
        menu.addAction(action)

    def _add_sidebar_section_action(self, menu, title: str, section_key: str) -> None:  # noqa: ANN001
        action = QAction(title, self)
        action.setCheckable(True)
        action.setChecked(True)
        action.toggled.connect(lambda _checked, key=section_key: self._apply_sidebar_section_visibility(key))
        menu.addAction(action)
        self.sidebar_section_actions[section_key] = action

    def _apply_sidebar_section_visibility(self, section_key: str) -> None:
        widget = self.sidebar_sections.get(section_key)
        action = self.sidebar_section_actions.get(section_key)
        if widget is None or action is None:
            return

        if section_key == "manifest":
            has_manifest = bool(self.manifest_entries)
            widget.setVisible(action.isChecked() and has_manifest)
            action.setEnabled(has_manifest)
            return

        widget.setVisible(action.isChecked())

    def _apply_all_sidebar_section_visibility(self) -> None:
        for section_key in self.sidebar_sections:
            self._apply_sidebar_section_visibility(section_key)

    def _build_legend_group(self) -> QGroupBox:
        group = QGroupBox("Legend")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        return group

    def _set_hovered_legend_label(self, highlight_label: str | None) -> None:
        if self.hovered_legend_label == highlight_label:
            return

        self.hovered_legend_label = highlight_label
        for widget in self.legend_entry_widgets:
            widget.set_hovered(widget.spec.highlight_label == highlight_label and highlight_label is not None)
        self._apply_visuals()

    def _add_legend_entry(self, spec: LegendEntrySpec) -> None:
        layout = self.legend_group.layout()
        if layout is None:
            return

        row = LegendEntryWidget(spec, self._set_hovered_legend_label)
        self.legend_entry_widgets.append(row)
        layout.addWidget(row)

    def _update_legend(self) -> None:
        layout = self.legend_group.layout()
        if layout is None:
            return

        self._set_hovered_legend_label(None)
        self.legend_entry_widgets.clear()

        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        layer_name = self.base_layer_combo.currentText() if self.base_layer_combo.count() else "Layer"
        self.legend_group.setTitle(f"Legend — {layer_name}")

        if self.dump is None:
            layout.addWidget(QLabel("Load or generate a world to see legend entries."))
            return

        entries, note = self._legend_entries(str(self.base_layer_combo.currentData()))
        for spec in entries:
            self._add_legend_entry(spec)

        if note is not None:
            note_label = QLabel(note)
            note_label.setWordWrap(True)
            layout.addWidget(note_label)

    def _build_generation_group(self) -> QGroupBox:
        group = QGroupBox("Generate preview")
        layout = QVBoxLayout(group)

        form = QFormLayout()
        seed_row = QWidget()
        seed_row_layout = QHBoxLayout(seed_row)
        seed_row_layout.setContentsMargins(0, 0, 0, 0)
        seed_row_layout.setSpacing(8)
        seed_row_layout.addWidget(self.generate_seed_spin, 1)
        seed_row_layout.addWidget(self.randomize_seed_button)

        form.addRow("Generator", self.generator_combo)
        form.addRow("Width", self.generate_width_spin)
        form.addRow("Height", self.generate_height_spin)
        form.addRow("Worlds", self.generate_count_spin)
        form.addRow("Seed", seed_row)
        layout.addLayout(form)

        layout.addWidget(self.generator_options_note)
        layout.addLayout(self.generation_option_form)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.generation_progress_label)
        layout.addWidget(self.generation_progress_bar)
        return group

    def _build_generated_overview_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.generated_overview_title_label = QLabel("Generated overview")
        self.generated_overview_title_label.setStyleSheet("font-size: 16px; font-weight: 600;")

        self.generated_overview_subtitle_label = QLabel(
            "Generate multiple worlds to compare them here, then click one to open it in the map view."
        )
        self.generated_overview_subtitle_label.setWordWrap(True)

        self.generated_overview_grid_container = QWidget()
        self.generated_overview_grid_layout = QGridLayout(self.generated_overview_grid_container)
        self.generated_overview_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.generated_overview_grid_layout.setHorizontalSpacing(12)
        self.generated_overview_grid_layout.setVerticalSpacing(12)

        self.generated_overview_scroll_area = GeneratedOverviewScrollArea()
        self.generated_overview_scroll_area.setWidgetResizable(True)
        self.generated_overview_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.generated_overview_scroll_area.setWidget(self.generated_overview_grid_container)
        self.generated_overview_scroll_area.resized.connect(self._update_generated_overview_card_sizes)

        layout.addWidget(self.generated_overview_title_label)
        layout.addWidget(self.generated_overview_subtitle_label)
        layout.addWidget(self.generated_overview_scroll_area, 1)

        self._rebuild_generated_overview_grid()
        return page

    def _build_controls_panel(self, open_button: QPushButton, fit_button: QPushButton) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        file_group = QGroupBox("File")
        file_layout = QVBoxLayout(file_group)
        file_layout.addWidget(self.file_label)

        file_buttons = QHBoxLayout()
        file_buttons.addWidget(open_button)
        file_buttons.addWidget(fit_button)
        file_layout.addLayout(file_buttons)
        layout.addWidget(file_group)

        generation_group = self._build_generation_group()
        layout.addWidget(generation_group)

        manifest_group = QGroupBox("Batch manifest")
        manifest_layout = QVBoxLayout(manifest_group)
        manifest_layout.addWidget(self.manifest_selector)
        layout.addWidget(manifest_group)

        render_group = QGroupBox("Rendering")
        render_form = QFormLayout(render_group)
        render_form.addRow("Base layer", self.base_layer_combo)
        render_form.addRow("Overlay scope", self.overlay_scope_combo)
        render_form.addRow(self.show_grid_checkbox)
        render_form.addRow(self.show_rivers_checkbox)
        render_form.addRow(self.dim_hidden_checkbox)
        layout.addWidget(render_group)
        layout.addWidget(self.legend_group)

        overlay_group = QGroupBox("Overlay coverage")
        overlay_layout = QVBoxLayout(overlay_group)
        overlay_layout.addWidget(self.overlay_summary_panel)
        layout.addWidget(overlay_group)

        labels_group = QGroupBox("Labels")
        labels_layout = QVBoxLayout(labels_group)
        labels_layout.addWidget(self.show_landmass_labels_checkbox)
        labels_layout.addWidget(self.show_biome_labels_checkbox)
        labels_layout.addWidget(self.show_river_labels_checkbox)
        layout.addWidget(labels_group)

        metadata_group = QGroupBox("Summary")
        metadata_layout = QVBoxLayout(metadata_group)
        metadata_layout.addWidget(self.summary_label)
        layout.addWidget(metadata_group)

        self.sidebar_sections = {
            "file": file_group,
            "generation": generation_group,
            "manifest": manifest_group,
            "render": render_group,
            "legend": self.legend_group,
            "overlay": overlay_group,
            "labels": labels_group,
            "summary": metadata_group,
        }

        layout.addStretch(1)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidget(panel)
        return scroll_area

    def _build_details_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        self.generated_preview_switch_group = QGroupBox("Generated worlds")
        generated_switch_layout = QVBoxLayout(self.generated_preview_switch_group)
        generated_switch_layout.setContentsMargins(10, 10, 10, 10)
        generated_switch_layout.setSpacing(8)
        generated_switch_layout.addWidget(self.generated_preview_selector)
        generated_switch_button_row = QHBoxLayout()
        generated_switch_button_row.addWidget(self.generated_preview_overview_button)
        generated_switch_button_row.addStretch(1)
        generated_switch_layout.addLayout(generated_switch_button_row)
        self.generated_preview_switch_group.hide()
        layout.addWidget(self.generated_preview_switch_group)

        title = QLabel("Hex inspector")
        title.setStyleSheet("font-weight: 600;")
        layout.addWidget(title)

        tools_group = QGroupBox("Inspector tools")
        tools_layout = QVBoxLayout(tools_group)
        tools_form = QFormLayout()
        tools_form.addRow("Column", self.coord_col_spin)
        tools_form.addRow("Row", self.coord_row_spin)
        tools_layout.addLayout(tools_form)

        primary_button_row = QHBoxLayout()
        primary_button_row.addWidget(self.jump_button)
        primary_button_row.addWidget(self.center_selected_button)
        tools_layout.addLayout(primary_button_row)

        secondary_button_row = QHBoxLayout()
        secondary_button_row.addWidget(self.clear_selection_button)
        secondary_button_row.addWidget(self.copy_details_button)
        tools_layout.addLayout(secondary_button_row)
        layout.addWidget(tools_group)

        self.info_panel.setMinimumHeight(280)
        layout.addWidget(self.info_panel)
        layout.addWidget(self.terrain_preview_group)
        layout.addWidget(self.resource_preview_group)
        layout.addStretch(1)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidget(panel)
        return scroll_area

    def _sync_manifest_selector(self) -> None:
        block_state = self.manifest_selector.blockSignals(True)
        self.manifest_selector.clear()
        for entry in self.manifest_entries:
            self.manifest_selector.addItem(entry.label)
        self.manifest_selector.blockSignals(block_state)

        self._apply_sidebar_section_visibility("manifest")

    def _format_loaded_file_label(self, path: Path) -> str:
        if self.current_manifest_path is None:
            return f"Loaded: {path}"
        return f"Manifest: {self.current_manifest_path}\nWorld: {path}"

    def _clear_generated_previews(self) -> None:
        if not self.generated_preview_results and self.center_stack.currentWidget() is self.view:
            self._sync_generated_preview_selector()
            self._update_generated_overview_navigation_action()
            return

        self.generated_preview_results = ()
        self.selected_generated_preview_index = None
        self.center_stack.setCurrentWidget(self.view)
        self._rebuild_generated_overview_grid()
        self._sync_generated_preview_selector()
        self._update_generated_overview_navigation_action()

    def _rebuild_generated_overview_grid(self) -> None:
        while self.generated_overview_grid_layout.count():
            item = self.generated_overview_grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.generated_overview_buttons.clear()

        if len(self.generated_preview_results) <= 1:
            self.generated_overview_title_label.setText("Generated overview")
            self.generated_overview_subtitle_label.setText(
                "Generate multiple worlds to compare them here, then click one to open it in the map view."
            )
            placeholder = QLabel(
                "Set Worlds above 1 in the Generate preview panel to build a comparison grid of generated worlds."
            )
            placeholder.setWordWrap(True)
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet(
                "padding: 24px; border: 1px dashed rgba(255, 255, 255, 0.12); border-radius: 10px;"
            )
            self.generated_overview_grid_layout.addWidget(placeholder, 0, 0)
            self.generated_overview_grid_layout.setColumnStretch(0, 1)
            return

        first_dump = self.generated_preview_results[0].dump
        seeds = [result.seed for result in self.generated_preview_results]
        seed_text = f"Seeds {seeds[0]}–{seeds[-1]}" if seeds else "Random seeds"
        self.generated_overview_title_label.setText(
            f"Generated overview — {len(self.generated_preview_results)} worlds"
        )
        self.generated_overview_subtitle_label.setText(
            f"{first_dump.generator_name} · {first_dump.requested_width} × {first_dump.requested_height} · {seed_text}. "
            "Click a preview card to inspect it, then use Back to overview to return here."
        )

        for index, result in enumerate(self.generated_preview_results):
            button = QToolButton()
            button.setCheckable(True)
            button.setAutoRaise(False)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            button.setIcon(QIcon(self._render_generated_overview_thumbnail(result.dump)))
            button.setIconSize(QPixmap(OVERVIEW_THUMBNAIL_WIDTH, OVERVIEW_THUMBNAIL_HEIGHT).size())
            button.setText(self._generated_overview_card_text(index, result))
            button.setToolTip(result.source_label)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(240)
            button.setStyleSheet(
                "QToolButton {"
                "background-color: #17191f;"
                "border: 1px solid #303640;"
                "border-radius: 10px;"
                "padding: 10px;"
                "font-weight: 600;"
                "}"
                "QToolButton:hover {"
                "border-color: #6ea8ff;"
                "background-color: #1c2128;"
                "}"
                "QToolButton:checked {"
                "border-color: #ffe082;"
                "background-color: #20252d;"
                "}"
            )
            button.clicked.connect(lambda _checked=False, preview_index=index: self._select_generated_preview(preview_index))

            row = index // OVERVIEW_CARD_COLUMNS
            column = index % OVERVIEW_CARD_COLUMNS
            self.generated_overview_grid_layout.addWidget(button, row, column)
            self.generated_overview_buttons.append(button)

        for column in range(OVERVIEW_CARD_COLUMNS):
            self.generated_overview_grid_layout.setColumnStretch(column, 1)

        self._sync_generated_overview_selection()
        self._update_generated_overview_card_sizes()

    def _generated_overview_card_text(self, index: int, result: GeneratedPreviewResult) -> str:
        hex_summary = result.dump.summary.get("hexes", {}) if isinstance(result.dump.summary.get("hexes"), dict) else {}
        land = int(hex_summary.get("land", 0))
        water = int(hex_summary.get("water", 0))
        river_count = int(result.dump.summary.get("river_count", 0))
        return "\n".join(
            [
                f"World {index + 1:02d} • seed {result.seed}",
                f"{result.dump.requested_width} × {result.dump.requested_height}",
                f"Land {land} · Water {water}",
                f"Rivers {river_count}",
            ]
        )

    def _render_generated_overview_thumbnail(self, dump: WorldgenDump) -> QPixmap:
        pixmap = QPixmap(OVERVIEW_THUMBNAIL_WIDTH, OVERVIEW_THUMBNAIL_HEIGHT)
        pixmap.fill(QColor("#15171c"))

        if not dump.hexes:
            return pixmap

        polygons = [(record, tuple(_hex_polygon(record.coord))) for record in dump.hexes]
        min_x = min(point.x() for _record, polygon in polygons for point in polygon)
        max_x = max(point.x() for _record, polygon in polygons for point in polygon)
        min_y = min(point.y() for _record, polygon in polygons for point in polygon)
        max_y = max(point.y() for _record, polygon in polygons for point in polygon)

        available_width = OVERVIEW_THUMBNAIL_WIDTH - 16
        available_height = OVERVIEW_THUMBNAIL_HEIGHT - 16
        bounds_width = max(max_x - min_x, 1.0)
        bounds_height = max(max_y - min_y, 1.0)
        scale = min(available_width / bounds_width, available_height / bounds_height)
        offset_x = (OVERVIEW_THUMBNAIL_WIDTH - bounds_width * scale) / 2
        offset_y = (OVERVIEW_THUMBNAIL_HEIGHT - bounds_height * scale) / 2

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(0, 0, 0, 52), 0.5))

        for record, polygon in polygons:
            mapped_polygon = QPolygonF(
                [
                    QPointF(
                        (point.x() - min_x) * scale + offset_x,
                        (point.y() - min_y) * scale + offset_y,
                    )
                    for point in polygon
                ]
            )
            if dump.runtime_tiles_by_coord:
                color = QColor(_runtime_terrain_color(dump, record))
            elif record.is_water:
                color = QColor(_water_color_for_record(record))
            else:
                color = QColor(BIOME_COLORS.get(record.biome_key, _stable_color(record.biome_key)))
            if not record.visible_in_runtime:
                color.setAlpha(95)
            painter.setBrush(QBrush(color))
            painter.drawPolygon(mapped_polygon)

        painter.end()
        return pixmap

    def _sync_generated_overview_selection(self) -> None:
        for index, button in enumerate(self.generated_overview_buttons):
            block_state = button.blockSignals(True)
            button.setChecked(index == self.selected_generated_preview_index)
            button.blockSignals(block_state)

    def _update_generated_overview_card_sizes(self) -> None:
        if not self.generated_overview_buttons:
            return

        viewport_width = self.generated_overview_scroll_area.viewport().width()
        if viewport_width <= 0:
            return

        columns = min(OVERVIEW_CARD_COLUMNS, max(1, len(self.generated_overview_buttons)))
        margins = self.generated_overview_grid_layout.contentsMargins()
        spacing = self.generated_overview_grid_layout.horizontalSpacing()
        if spacing < 0:
            spacing = 0

        available_width = viewport_width - margins.left() - margins.right() - spacing * (columns - 1)
        if available_width <= 0:
            return

        card_width = max(OVERVIEW_CARD_MIN_WIDTH, available_width // columns)
        icon_width = max(110, card_width - 48)
        icon_height = max(75, round(icon_width * OVERVIEW_THUMBNAIL_HEIGHT / OVERVIEW_THUMBNAIL_WIDTH))
        button_height = icon_height + 96
        icon_size = QSize(icon_width, icon_height)

        for button in self.generated_overview_buttons:
            button.setFixedWidth(card_width)
            button.setIconSize(icon_size)
            button.setMinimumHeight(button_height)

    def _sync_generated_preview_selector(self) -> None:
        has_generated_batch = len(self.generated_preview_results) > 1
        self.generated_preview_switch_group.setVisible(has_generated_batch)

        block_state = self.generated_preview_selector.blockSignals(True)
        self.generated_preview_selector.clear()
        for index, result in enumerate(self.generated_preview_results, start=1):
            self.generated_preview_selector.addItem(f"World {index:02d} • seed {result.seed}", index - 1)

        if has_generated_batch and self.selected_generated_preview_index is not None:
            self.generated_preview_selector.setCurrentIndex(self.selected_generated_preview_index)

        self.generated_preview_selector.blockSignals(block_state)

    def _select_generated_preview(self, index: int, *, show_detail: bool = True) -> None:
        if index < 0 or index >= len(self.generated_preview_results):
            return

        self.selected_generated_preview_index = index
        self._sync_generated_overview_selection()
        self._sync_generated_preview_selector()

        result = self.generated_preview_results[index]
        self._apply_loaded_dump(result.dump, result.source_label)

        if show_detail:
            self.center_stack.setCurrentWidget(self.view)
            self.statusBar().showMessage(
                f"Loaded generated world {index + 1}/{len(self.generated_preview_results)} (seed {result.seed})"
            )

        self._update_generated_overview_navigation_action()

    def _on_generated_preview_selector_changed(self, index: int) -> None:
        if index < 0:
            return

        self._select_generated_preview(index)

    def _show_generated_overview(self) -> None:
        if len(self.generated_preview_results) <= 1:
            self.statusBar().showMessage("No generated overview is available yet")
            return

        self.center_stack.setCurrentWidget(self.generated_overview_page)
        self._update_generated_overview_card_sizes()
        self._update_generated_overview_navigation_action()
        self.statusBar().showMessage("Showing generated overview")

    def _update_generated_overview_navigation_action(self) -> None:
        has_overview = len(self.generated_preview_results) > 1
        is_detail_view = self.center_stack.currentWidget() is self.view
        self.back_to_overview_action.setEnabled(has_overview and is_detail_view)
        self.generated_preview_overview_button.setEnabled(has_overview and is_detail_view)

    def _current_generator_spec(self) -> OfflineGeneratorSpec:
        if not self.generator_specs:
            raise ValueError(self.generation_error or "Generator previews are unavailable in this environment.")
        return resolve_offline_generator(str(self.generator_combo.currentData()))

    def _sync_generation_option_controls(self) -> None:
        if not self.generator_specs:
            self.generator_combo.setEnabled(False)
            self.generate_count_spin.setEnabled(False)
            self.generate_button.setEnabled(False)
            message = "Generator previews are unavailable in this environment."
            if self.generation_error is not None:
                message = f"{message}\n\n{self.generation_error}"
            self.generator_options_note.setText(message)
            for label, combo in self.generation_option_controls.values():
                label.hide()
                combo.hide()
            return

        current_spec = self._current_generator_spec()
        active_options = {option.key: option for option in current_spec.options}
        self.generator_combo.setEnabled(True)
        self.generate_count_spin.setEnabled(True)
        self.generate_button.setEnabled(True)

        if current_spec.options:
            self.generator_options_note.setText("Generator-specific parameters for the selected offline preview generator.")
        else:
            self.generator_options_note.setText("This generator has no extra preview parameters.")

        for key, (label, combo) in self.generation_option_controls.items():
            option = active_options.get(key)
            is_visible = option is not None
            label.setVisible(is_visible)
            combo.setVisible(is_visible)
            combo.setEnabled(is_visible)
            if option is None:
                continue

            current_value = str(combo.currentData()) if combo.count() else None
            combo.blockSignals(True)
            combo.clear()
            for display_name, value in option.choices:
                combo.addItem(display_name, value)

            if current_value not in option.allowed_values:
                current_value = option.default
            index = combo.findData(current_value)
            if index >= 0:
                combo.setCurrentIndex(index)
            combo.blockSignals(False)

    def _randomize_seed(self) -> None:
        self.generate_seed_spin.setValue(generate_random_seed())

    def _update_generation_button_text(self) -> None:
        if self.generation_thread is not None and self.generation_thread.isRunning():
            return

        count = self.generate_count_spin.value()
        if count == 1:
            self.generate_button.setText("Generate preview")
            return

        self.generate_button.setText(f"Generate {count} previews")

    def _generation_seed_batch(self, count: int) -> tuple[int, ...]:
        requested_seed = self.generate_seed_spin.value()
        if requested_seed > 0:
            return tuple(((requested_seed - 1 + offset) % MAX_PREVIEW_SEED) + 1 for offset in range(count))

        generated_seeds: list[int] = []
        seen_seeds: set[int] = set()
        while len(generated_seeds) < count:
            seed = generate_random_seed()
            if seed in seen_seeds:
                continue
            seen_seeds.add(seed)
            generated_seeds.append(seed)
        return tuple(generated_seeds)

    def _generate_preview(self) -> None:
        if self.generation_thread is not None and self.generation_thread.isRunning():
            self.statusBar().showMessage("Preview generation is already running")
            return

        if not self.generator_specs:
            QMessageBox.warning(
                self,
                "Generation unavailable",
                self.generation_error or "Generator previews are unavailable in this environment.",
            )
            return

        generator_spec = self._current_generator_spec()
        raw_options: dict[str, str] = {}
        for option in generator_spec.options:
            combo = self.generation_option_controls[option.key][1]
            raw_options[option.key] = str(combo.currentData())

        sanitized_options = generator_spec.sanitize_options(raw_options)
        width = self.generate_width_spin.value()
        height = self.generate_height_spin.value()
        world_count = self.generate_count_spin.value()
        seeds = self._generation_seed_batch(world_count)

        request = PreviewGenerationRequest(
            generator_spec=generator_spec,
            width=width,
            height=height,
            seeds=seeds,
            options=sanitized_options,
        )

        self.generation_thread = QThread(self)
        self.generation_worker = PreviewGenerationWorker(request)
        self.generation_worker.moveToThread(self.generation_thread)

        self.generation_thread.started.connect(self.generation_worker.run)
        self.generation_worker.progress_changed.connect(self._update_generation_progress)
        self.generation_worker.generation_succeeded.connect(self._on_generation_succeeded)
        self.generation_worker.generation_failed.connect(self._on_generation_failed)
        self.generation_worker.generation_succeeded.connect(self.generation_thread.quit)
        self.generation_worker.generation_failed.connect(self.generation_thread.quit)
        self.generation_thread.finished.connect(self._on_generation_thread_finished)
        self.generation_thread.finished.connect(self.generation_worker.deleteLater)
        self.generation_thread.finished.connect(self.generation_thread.deleteLater)

        self._set_generation_running(True, "Starting preview generation")
        self.generation_thread.start()

    def _build_generated_label(
        self,
        generator_spec: OfflineGeneratorSpec,
        width: int,
        height: int,
        seed: int,
        options: dict[str, str],
    ) -> str:
        return _build_generated_label_text(generator_spec, width, height, seed, options)

    def _update_generation_progress(self, step: int, total: int, message: str) -> None:
        self.generation_progress_label.setText(message)
        self.generation_progress_bar.setRange(0, max(1, total))
        self.generation_progress_bar.setValue(min(step, total))
        self.statusBar().showMessage(message)

    def _on_generation_succeeded(self, generated_obj: object) -> None:
        if not isinstance(generated_obj, tuple) or not generated_obj:
            self._on_generation_failed("The generated preview payload could not be loaded into the viewer.")
            return

        if not all(isinstance(result, GeneratedPreviewResult) for result in generated_obj):
            self._on_generation_failed("The generated preview results were malformed.")
            return

        generated_results = tuple(generated_obj)
        if len(generated_results) == 1 and self.generate_seed_spin.value() == 0:
            self.generate_seed_spin.setValue(generated_results[0].seed)

        self.current_manifest_path = None
        self.manifest_entries = ()
        self._sync_manifest_selector()

        if len(generated_results) == 1:
            self._clear_generated_previews()
            self._apply_loaded_dump(generated_results[0].dump, generated_results[0].source_label)
            self.center_stack.setCurrentWidget(self.view)
            self.statusBar().showMessage(f"Generated preview for seed {generated_results[0].seed}")
            self._update_generated_overview_navigation_action()
            return

        self.generated_preview_results = generated_results
        self.selected_generated_preview_index = 0
        self._rebuild_generated_overview_grid()
        self._sync_generated_preview_selector()
        self._select_generated_preview(0, show_detail=False)
        self._show_generated_overview()

    def _on_generation_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Generation failed", message)
        self.statusBar().showMessage(f"Generation failed: {message}")

    def _on_generation_thread_finished(self) -> None:
        self.generation_thread = None
        self.generation_worker = None
        self._set_generation_running(False)

    def _set_generation_running(self, running: bool, message: str | None = None) -> None:
        if running:
            self.generator_combo.setEnabled(False)
            self.generate_width_spin.setEnabled(False)
            self.generate_height_spin.setEnabled(False)
            self.generate_count_spin.setEnabled(False)
            self.generate_seed_spin.setEnabled(False)
            self.randomize_seed_button.setEnabled(False)
            self.generate_button.setEnabled(False)
            self.generate_button.setText("Generating…")
            self.generate_action.setEnabled(False)
            self.randomize_seed_action.setEnabled(False)
            self.quit_action.setEnabled(False)
            for label, combo in self.generation_option_controls.values():
                if label.isVisible():
                    combo.setEnabled(False)

            self.generation_progress_label.setText(message or "Generating preview")
            self.generation_progress_label.show()
            self.generation_progress_bar.setRange(0, 6)
            self.generation_progress_bar.setValue(0)
            self.generation_progress_bar.show()
            self.statusBar().showMessage(message or "Generating preview")
            return

        self.generation_progress_label.hide()
        self.generation_progress_bar.hide()
        self.randomize_seed_action.setEnabled(True)
        self.quit_action.setEnabled(True)
        self._sync_generation_option_controls()
        self.generate_count_spin.setEnabled(True)
        self._update_generation_button_text()

    def _jump_to_coord(self) -> None:
        if self.dump is None:
            return

        coord = (self.coord_col_spin.value(), self.coord_row_spin.value())
        if coord not in self.dump.hexes_by_coord:
            self.statusBar().showMessage(f"Hex {coord[0]}, {coord[1]} is not present in this dump")
            return

        self._select_hex(coord)
        self._center_on_coord(coord)

    def _center_on_coord(self, coord: HexCoord) -> None:
        self.view.centerOn(_hex_center(coord))

    def _center_on_selected_hex(self) -> None:
        if self.selected_coord is None:
            self.statusBar().showMessage("Select a hex first")
            return

        self._center_on_coord(self.selected_coord)
        self.statusBar().showMessage(f"Centered on hex {self.selected_coord[0]}, {self.selected_coord[1]}")

    def _clear_selection(self) -> None:
        if self.selected_coord is None:
            return

        self.selected_coord = None
        self._apply_visuals()
        self._update_info_panel()
        self._update_asset_preview_panels()
        self._update_selection_controls()
        self.statusBar().showMessage("Selection cleared")

    def _update_asset_preview_panels(self) -> None:
        if self.dump is None or self.selected_coord is None:
            self.terrain_preview_group.clear()
            self.resource_preview_group.clear()
            return

        record = self.dump.hexes_by_coord[self.selected_coord]

        terrain_preview = resolve_terrain_asset_preview(_runtime_terrain_key(self.dump, record))
        if terrain_preview is None:
            terrain_key = _runtime_terrain_key(self.dump, record) or record.terrain or "unknown"
            self.terrain_preview_group.clear(f"No terrain preview metadata was found for '{terrain_key}'.")
        else:
            self._apply_asset_preview_group(self.terrain_preview_group, terrain_preview)

        resource_key = _runtime_resource_key(self.dump, record)
        if resource_key is None:
            self.resource_preview_group.clear("No runtime resource is placed on the selected hex.")
            return

        resource_preview = resolve_resource_asset_preview(resource_key, is_water=record.is_water)
        if resource_preview is None:
            self.resource_preview_group.clear(f"No resource preview metadata was found for '{resource_key}'.")
            return

        self._apply_asset_preview_group(self.resource_preview_group, resource_preview)

    def _apply_asset_preview_group(self, group: AssetPreviewGroupWidget, preview: AssetPreviewInfo) -> None:
        primary_pixmap = self._load_preview_pixmap(preview.primary_image_path)
        model_preview_path = render_model_preview_image(preview)
        model_pixmap = self._load_preview_pixmap(model_preview_path)
        group.set_preview(preview, primary_pixmap=primary_pixmap, model_pixmap=model_pixmap)

    def _load_preview_pixmap(self, path: Path | None) -> QPixmap | None:
        if path is None or not path.exists():
            return None

        cached = self.preview_pixmaps_by_path.get(path)
        if cached is not None:
            return cached

        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self.preview_pixmaps_by_path[path] = None
            return None

        self.preview_pixmaps_by_path[path] = pixmap
        return pixmap

    def _copy_current_details(self) -> None:
        if self.dump is None:
            return

        QApplication.clipboard().setText(self.info_panel.toPlainText())
        self.statusBar().showMessage("Inspector text copied to clipboard")

    def _update_coordinate_ranges(self) -> None:
        if self.dump is None or not self.dump.hexes:
            max_col = 0
            max_row = 0
        else:
            max_col = max(record.coord[0] for record in self.dump.hexes)
            max_row = max(record.coord[1] for record in self.dump.hexes)

        self.coord_col_spin.setRange(0, max_col)
        self.coord_row_spin.setRange(0, max_row)

    def _sync_coordinate_inputs(self, coord: HexCoord | None = None) -> None:
        if coord is None:
            if self.selected_coord is not None:
                coord = self.selected_coord
            elif self.dump is not None and self.dump.hexes:
                coord = next((record.coord for record in self.dump.hexes if record.visible_in_runtime), self.dump.hexes[0].coord)
            else:
                coord = (0, 0)

        self.coord_col_spin.setValue(coord[0])
        self.coord_row_spin.setValue(coord[1])

    def _update_selection_controls(self) -> None:
        has_dump = self.dump is not None
        has_selection = self.selected_coord is not None

        self.jump_button.setEnabled(has_dump)
        self.copy_details_button.setEnabled(has_dump)
        self.copy_details_action.setEnabled(has_dump)

        self.center_selected_button.setEnabled(has_selection)
        self.clear_selection_button.setEnabled(has_selection)
        self.center_selected_action.setEnabled(has_selection)
        self.clear_selection_action.setEnabled(has_selection)

    def _update_overlay_summary(self) -> None:
        if self.dump is None:
            self.overlay_summary_panel.setPlainText("Load or generate a world to inspect overlay coverage.")
            return

        records = self._overlay_records_for_scope()
        if not records:
            self.overlay_summary_panel.setPlainText("No hexes are available for the current overlay scope.")
            return

        mode = str(self.base_layer_combo.currentData())
        counts = Counter(self._overlay_bucket_label(record, mode) for record in records)
        total = len(records)

        lines = [
            f"Layer: {self.base_layer_combo.currentText()}",
            f"Scope: {self.overlay_scope_combo.currentText()}",
            f"Hexes counted: {total}",
        ]

        if mode == "altitude":
            lines.append(f"Sea level: {_heightmap_sealevel(self.dump):.0f}")
        elif mode == "rivers":
            river_payloads = [river for river in self.dump.rivers if isinstance(river, dict)]
            river_lengths = [int(river.get("length", 0)) for river in river_payloads]
            river_mouths = sum(1 for river in river_payloads if river.get("mouth") is not None)
            river_networks = {
                str(river.get("network_id") or river.get("id") or "")
                for river in river_payloads
                if river.get("network_id") or river.get("id")
            }
            lines.append(f"River chains: {len(river_lengths)}")
            lines.append(f"River networks: {len(river_networks)}")
            lines.append(f"River segments: {sum(river_lengths)}")
            if river_lengths:
                lines.append(f"Average chain length: {sum(river_lengths) / len(river_lengths):.1f}")
                lines.append(f"Longest chain: {max(river_lengths)}")
            lines.append(f"Named mouths: {river_mouths}")
            lines.append(f"Headwater tiles: {counts.get('Headwaters', 0)}")
            lines.append(f"Confluence tiles: {counts.get('River confluence', 0)}")
            lines.append(f"Braid tiles: {counts.get('River braid', 0)}")
            lines.append(f"Connector tiles: {counts.get('River connector', 0)}")

            top_systems: list[dict[str, object]] = []
            seen_networks: set[str] = set()
            for river in sorted(river_payloads, key=lambda current: int(current.get("length", 0)), reverse=True):
                network_id = str(river.get("network_id") or river.get("id") or "")
                if not network_id or network_id in seen_networks:
                    continue
                seen_networks.add(network_id)
                top_systems.append(river)
                if len(top_systems) >= 5:
                    break

            if top_systems:
                lines.append("")
                lines.append("Top systems:")
                for river in top_systems:
                    name = str(river.get("display_name") or river.get("network_id") or river.get("id") or "Unnamed river")
                    length = int(river.get("length", 0))
                    branch_kind = river.get("branch_kind")
                    branch_text = (
                        f" · {str(branch_kind).replace('_', ' ').strip().title()}"
                        if isinstance(branch_kind, str) and branch_kind.strip()
                        else ""
                    )
                    lines.append(f"  {name} — {length} segments{branch_text}")
        elif mode == "moisture":
            lines.append(
                f"Moisture range: {self.dump.moisture_range[0]:.2f} – {self.dump.moisture_range[1]:.2f}"
            )
        elif mode == "resources":
            resource_keys = {
                _runtime_resource_key(self.dump, record)
                for record in records
                if _runtime_resource_key(self.dump, record) is not None
            }
            resource_tile_count = sum(1 for record in records if _runtime_resource_key(self.dump, record) is not None)
            lines.append(f"Distinct resources: {len(resource_keys)}")
            lines.append(f"Resource-bearing tiles: {resource_tile_count}")

        lines.append("")

        ordered_items = self._ordered_overlay_counts(mode, counts)
        display_items = ordered_items[:MAX_OVERLAY_SUMMARY_ITEMS]
        hidden_items = ordered_items[MAX_OVERLAY_SUMMARY_ITEMS:]
        hidden_count = sum(count for _, count in hidden_items)

        label_width = max(len(label) for label, _ in display_items + ([("Other categories", hidden_count)] if hidden_count else []))
        for label, count in display_items:
            percentage = count / total * 100
            lines.append(f"{label:<{label_width}}  {percentage:>5.1f}%  {count:>5}")

        if hidden_count:
            hidden_percentage = hidden_count / total * 100
            lines.append(f"{'Other categories':<{label_width}}  {hidden_percentage:>5.1f}%  {hidden_count:>5}")

        self.overlay_summary_panel.setPlainText("\n".join(lines))

    def _overlay_records_for_scope(self) -> tuple[HexRecord, ...]:
        if self.dump is None:
            return ()

        scope = str(self.overlay_scope_combo.currentData())
        if scope == "runtime-visible":
            visible_records = tuple(record for record in self.dump.hexes if record.visible_in_runtime)
            if visible_records:
                return visible_records

        return self.dump.hexes

    def _ordered_overlay_counts(self, mode: str, counts: Counter[str]) -> list[tuple[str, int]]:
        preferred_order = OVERLAY_BUCKET_ORDER.get(mode)
        if preferred_order is None:
            return sorted(counts.items(), key=lambda item: (-item[1], item[0]))

        ordered_items: list[tuple[str, int]] = []
        seen: set[str] = set()
        for label in preferred_order:
            if label in counts:
                ordered_items.append((label, counts[label]))
                seen.add(label)

        remainder = sorted(((label, count) for label, count in counts.items() if label not in seen), key=lambda item: (-item[1], item[0]))
        ordered_items.extend(remainder)
        return ordered_items

    def _legend_entries_from_records(self, mode: str) -> list[LegendEntrySpec]:
        if self.dump is None:
            return []

        counts: Counter[str] = Counter()
        colors: dict[str, QColor] = {}
        for record in self.dump.hexes:
            label = self._overlay_bucket_label(record, mode)
            counts[label] += 1
            if label not in colors:
                colors[label] = QColor(self._color_for_hex(record, mode))

        return [
            LegendEntrySpec(colors[label], label, label)
            for label, _count in self._ordered_overlay_counts(mode, counts)
        ]

    def _overlay_bucket_label(self, record: HexRecord, mode: str) -> str:
        if self.dump is None:
            return "Unknown"

        if mode == "biome":
            if record.is_water:
                return _overlay_water_label(record)
            return record.biome_title

        if mode == "geoform":
            return record.geoform_title or _title_from_identifier(record.geoform_type or "unknown")

        if mode == "territory":
            if record.territory_id is None:
                return "Unclaimed water" if record.is_water else "Unclaimed land"
            territory_name = record.territory_name or self.dump.territory_names_by_id.get(record.territory_id)
            if territory_name is None:
                return f"Territory {record.territory_id}"
            return territory_name

        if mode == "rivers":
            return river_role_label_for_record(record)

        if mode == "runtime-terrain":
            return _runtime_terrain_label(self.dump, record)

        if mode == "resources":
            return _resource_label(self.dump, record)

        if mode == "visibility":
            if not record.visible_in_runtime:
                return "Outside runtime bounds"
            return "Visible runtime water" if record.is_water else "Visible runtime land"

        if mode == "altitude":
            return _altitude_bucket_label(self.dump, record)

        if mode == "moisture":
            return _moisture_bucket_label(self.dump, record)

        return "Unknown"

    def _color_for_hex(self, record: HexRecord, mode: str | None = None) -> QColor:
        if self.dump is None:
            return QColor("#777777")

        active_mode = mode or str(self.base_layer_combo.currentData())
        if active_mode == "biome":
            if record.is_water:
                return _water_color_for_record(record)
            return QColor(BIOME_COLORS.get(record.biome_key, _stable_color(record.biome_key)))
        if active_mode == "altitude":
            return _altitude_color(record.altitude, self.dump.altitude_range, record.is_water)
        if active_mode == "moisture":
            return _moisture_color(record.moisture, self.dump.moisture_range)
        if active_mode == "geoform":
            geoform_key = record.geoform_type or record.geoform_title or "unknown"
            return QColor(GEOFORM_COLORS.get(geoform_key, _stable_color(geoform_key)))
        if active_mode == "territory":
            if record.territory_id is None:
                return QColor("#37404a") if record.is_water else QColor("#4e553f")
            return _stable_color(f"territory:{record.territory_id}", saturation=180, value=220)
        if active_mode == "rivers":
            river_role = river_role_label_for_record(record)
            return QColor(RIVER_COLORS.get(river_role, _stable_color(f"river:{river_role}")))
        if active_mode == "runtime-terrain":
            return _runtime_terrain_color(self.dump, record)
        if active_mode == "resources":
            return _resource_color(self.dump, record)
        if active_mode == "visibility":
            if record.visible_in_runtime:
                return QColor("#9ccc65") if record.is_land else QColor("#4fc3f7")
            return QColor("#42454f")

        return QColor("#777777")

    def _legend_entries(self, mode: str) -> tuple[list[LegendEntrySpec], str | None]:
        if self.dump is None:
            return [], None

        if mode == "biome":
            return self._legend_entries_from_records(mode), "Water hexes use waterbody colors in biome mode because raw oceans still carry climate-biome metadata underneath."

        if mode == "geoform":
            return [
                LegendEntrySpec(GEOFORM_COLORS["continent"], "Continent", "Continent"),
                LegendEntrySpec(GEOFORM_COLORS["island"], "Island", "Island"),
                LegendEntrySpec(GEOFORM_COLORS["islet"], "Islet", "Islet"),
                LegendEntrySpec(GEOFORM_COLORS["lake"], "Lake", "Lake"),
                LegendEntrySpec(GEOFORM_COLORS["sea"], "Sea", "Sea"),
                LegendEntrySpec(GEOFORM_COLORS["ocean"], "Ocean", "Ocean"),
            ], None

        if mode == "runtime-terrain":
            return self._legend_entries_from_records(mode), "Runtime Terrain legend is generated from the terrain variants present in the current dump, so hills, snow, and other subtypes appear when available."

        if mode == "resources":
            entries = self._legend_entries_from_records(mode)
            note = "Resource legend is generated from the runtime resource keys present in the current dump."
            if len(entries) > MAX_RESOURCE_LEGEND_ITEMS:
                hidden_count = len(entries) - MAX_RESOURCE_LEGEND_ITEMS
                entries = entries[:MAX_RESOURCE_LEGEND_ITEMS]
                note += f" Showing the first {MAX_RESOURCE_LEGEND_ITEMS} entries; {hidden_count} more are hidden."
            if any(not record.visible_in_runtime for record in self.dump.hexes):
                note += " Tiles outside the runtime-visible rectangle are listed separately because they do not receive runtime resource assignments."
            return entries, note

        if mode == "visibility":
            return [
                LegendEntrySpec(QColor("#9ccc65"), "Visible runtime land", "Visible runtime land"),
                LegendEntrySpec(QColor("#4fc3f7"), "Visible runtime water", "Visible runtime water"),
                LegendEntrySpec(QColor("#42454f"), "Outside runtime bounds", "Outside runtime bounds"),
            ], None

        if mode == "territory":
            territory_ids = sorted({record.territory_id for record in self.dump.hexes if record.territory_id is not None})
            entries: list[LegendEntrySpec] = [
                LegendEntrySpec(QColor("#4e553f"), "Unclaimed land", "Unclaimed land"),
                LegendEntrySpec(QColor("#37404a"), "Unclaimed water", "Unclaimed water"),
            ]
            for territory_id in territory_ids[:MAX_TERRITORY_LEGEND_ITEMS]:
                territory_name = self.dump.territory_names_by_id.get(territory_id, f"Territory {territory_id}")
                entries.append(
                    LegendEntrySpec(
                        _stable_color(f"territory:{territory_id}", saturation=180, value=220),
                        territory_name,
                        territory_name,
                    )
                )

            note = None
            if len(territory_ids) > MAX_TERRITORY_LEGEND_ITEMS:
                note = f"Showing the first {MAX_TERRITORY_LEGEND_ITEMS} territory colors."
            return entries, note

        if mode == "rivers":
            return [
                LegendEntrySpec(RIVER_COLORS["Headwaters"], "Headwaters", "Headwaters"),
                LegendEntrySpec(RIVER_COLORS["River braid"], "River braid", "River braid"),
                LegendEntrySpec(RIVER_COLORS["River connector"], "River connector", "River connector"),
                LegendEntrySpec(RIVER_COLORS["River channel"], "River channel", "River channel"),
                LegendEntrySpec(RIVER_COLORS["River confluence"], "River confluence", "River confluence"),
                LegendEntrySpec(RIVER_COLORS["River mouth"], "River mouth", "River mouth"),
                LegendEntrySpec(RIVER_COLORS["Land without river"], "Land without river", "Land without river"),
                LegendEntrySpec(RIVER_COLORS["Water without river"], "Water without river", "Water without river"),
            ], "River mode keeps the channel lines visible even when the normal river overlay toggle is off so hydrology can be inspected directly, and now distinguishes braids plus connector branches from ordinary channels."

        if mode == "altitude":
            low, high = self.dump.altitude_range
            sealevel = _heightmap_sealevel(self.dump)
            low_land = min(high, max(low, sealevel + 6.0))
            mid_land = (low_land + high) / 2 if high > low_land else high
            return [
                LegendEntrySpec(_altitude_color(low, self.dump.altitude_range, True), f"Deep water ({low:.0f})", "Deep water"),
                LegendEntrySpec(_altitude_color(sealevel, self.dump.altitude_range, True), f"Shallow water ({sealevel:.0f})", "Shallow water"),
                LegendEntrySpec(_altitude_color(low_land, self.dump.altitude_range, False), f"Low land ({low_land:.0f})", "Low land"),
                LegendEntrySpec(_altitude_color(mid_land, self.dump.altitude_range, False), f"High land ({mid_land:.0f})", "High land"),
                LegendEntrySpec(_altitude_color(high, self.dump.altitude_range, False), f"Peaks ({high:.0f})", "Peaks"),
            ], None

        if mode == "moisture":
            low, high = self.dump.moisture_range
            mid = (low + high) / 2
            return [
                LegendEntrySpec(_moisture_color(low, self.dump.moisture_range), f"Dry ({low:.2f})", "Dry"),
                LegendEntrySpec(_moisture_color(mid, self.dump.moisture_range), f"Balanced ({mid:.2f})", "Balanced"),
                LegendEntrySpec(_moisture_color(high, self.dump.moisture_range), f"Wet ({high:.2f})", "Wet"),
            ], None

        return [], None


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="View SCiv world generation exports with overlay controls.")
    parser.add_argument("path", nargs="?", type=Path, help="Optional world dump or batch manifest to load on startup.")
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="Print a short summary for the supplied dump or manifest and exit without opening the UI.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.inspect:
        if args.path is None:
            raise SystemExit("--inspect requires a dump or manifest path.")

        manifest_entries = load_manifest(args.path)
        if manifest_entries is not None:
            print(f"Manifest: {args.path}")
            print(f"Entries: {len(manifest_entries)}")
            for entry in manifest_entries[:5]:
                print(f"- {entry.label}")
            return 0

        dump = load_worldgen_dump(args.path)
        print(format_dump_summary(dump))
        return 0

    app = QApplication(sys.argv if argv is None else [sys.argv[0], *argv])
    window = WorldgenViewerWindow(initial_path=args.path)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import hashlib
import math
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PyQt6.QtCore import QObject, QPointF, QThread, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor, QFont, QFontDatabase, QPainter, QPen, QPixmap, QPolygonF
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QFileDialog,
    QFormLayout,
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
    QSplitter,
    QToolBar,
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
    resource_display_text,
    river_role_label as river_role_label_for_record,
    terrain_display_name,
)


HEX_RADIUS = 18.0
SQRT3 = 3**0.5
HEX_VERTEX_ANGLES = (0, 60, 120, 180, 240, 300)
MAX_TERRITORY_LEGEND_ITEMS = 8
MAX_RESOURCE_LEGEND_ITEMS = 18
MAX_OVERLAY_SUMMARY_ITEMS = 12
BIOME_COLORS = {
    "arctic": QColor("#b6d6ff"),
    "desert": QColor("#d8c07a"),
    "frozen": QColor("#d9f1ff"),
    "grasslands": QColor("#8dbb5a"),
    "jungle": QColor("#2f8f4e"),
    "plains": QColor("#b8c16d"),
    "savannah": QColor("#b6a25e"),
    "swamp": QColor("#4f7d59"),
    "taiga": QColor("#6f9c7d"),
    "tundra": QColor("#9ab5ad"),
}
GEOFORM_COLORS = {
    "continent": QColor("#5d8c46"),
    "island": QColor("#93b86b"),
    "islet": QColor("#c8d5a3"),
    "lake": QColor("#4b89c8"),
    "ocean": QColor("#2b4f7f"),
    "sea": QColor("#34669c"),
}
TERRAIN_COLORS = {
    "coast": QColor("#4e9cc9"),
    "desert": QColor("#c6b46f"),
    "forest": QColor("#5a8d4e"),
    "grasslands": QColor("#7aac55"),
    "hills": QColor("#92775a"),
    "jungle": QColor("#2f8f4e"),
    "lake": QColor("#5d97c7"),
    "mountains": QColor("#8d8c92"),
    "ocean": QColor("#2f507c"),
    "plains": QColor("#9eaf66"),
    "savannah": QColor("#b6a25e"),
    "scrubland": QColor("#9fa65d"),
    "sea_ice": QColor("#dbeeff"),
    "snow": QColor("#edf6ff"),
    "tundra": QColor("#a8b5b0"),
    "volcano": QColor("#b85b47"),
}
RIVER_COLORS = {
    "Headwaters": QColor("#88f1c2"),
    "River braid": QColor("#79ddff"),
    "River connector": QColor("#5eafff"),
    "River channel": QColor("#4fc3f7"),
    "River confluence": QColor("#1eb5ff"),
    "River mouth": QColor("#9fe8ff"),
    "Land without river": QColor("#5d6c50"),
    "Water without river": QColor("#24394f"),
}
LABEL_COLORS = {
    "landmasses": QColor("#f2f1c2"),
    "biome_regions": QColor("#d1f0d7"),
    "rivers": QColor("#9ed2ff"),
}
RESOURCE_SPECIAL_COLORS = {
    "No resource": QColor("#6d7278"),
    "Outside runtime bounds": QColor("#42454f"),
}
OVERLAY_BUCKET_ORDER = {
    "biome": (
        "Ocean / deep sea",
        "Coast / shallow water",
        "Lake",
        "Sea ice",
        "Arctic",
        "Desert",
        "Frozen",
        "Grasslands",
        "Jungle",
        "Plains",
        "Savannah",
        "Swamp",
        "Taiga",
        "Tundra",
    ),
    "altitude": ("Deep water", "Shallow water", "Low land", "High land", "Peaks"),
    "moisture": ("Dry", "Balanced", "Wet"),
    "resources": ("No resource", "Outside runtime bounds"),
    "rivers": (
        "Headwaters",
        "River braid",
        "River connector",
        "River channel",
        "River confluence",
        "River mouth",
        "Land without river",
        "Water without river",
    ),
    "visibility": ("Visible runtime land", "Visible runtime water", "Outside runtime bounds"),
}


@dataclass(frozen=True, slots=True)
class LegendEntrySpec:
    color: QColor
    text: str
    highlight_label: str | None


@dataclass(frozen=True, slots=True)
class PreviewGenerationRequest:
    generator_spec: OfflineGeneratorSpec
    width: int
    height: int
    seed: int
    options: dict[str, str]


class PreviewGenerationWorker(QObject):
    progress_changed = pyqtSignal(int, int, str)
    generation_succeeded = pyqtSignal(object, str, int)
    generation_failed = pyqtSignal(str)

    def __init__(self, request: PreviewGenerationRequest) -> None:
        super().__init__()
        self.request = request

    def run(self) -> None:
        try:
            payload = generate_world_payload(
                self.request.generator_spec,
                width=self.request.width,
                height=self.request.height,
                seed=self.request.seed,
                options=self.request.options,
                debug=False,
                source="viewer",
                extra_meta={
                    "viewer_preview": {
                        "generated_in_viewer": True,
                    }
                },
                progress_callback=self._emit_generation_progress,
            )
            self.progress_changed.emit(6, 6, "Loading preview dump")
            dump = load_worldgen_payload(payload, path=Path("<generated>"))
            source_label = _build_generated_label_text(
                self.request.generator_spec,
                self.request.width,
                self.request.height,
                self.request.seed,
                self.request.options,
            )
        except Exception as exc:  # noqa: BLE001
            self.generation_failed.emit(str(exc))
            return

        self.generation_succeeded.emit(dump, source_label, self.request.seed)

    def _emit_generation_progress(self, step: int, total: int, message: str) -> None:
        self.progress_changed.emit(step, total + 1, message)


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


class LegendEntryWidget(QFrame):
    def __init__(self, spec: LegendEntrySpec, on_hover_changed: Callable[[str | None], None]) -> None:
        super().__init__()
        self.spec = spec
        self._on_hover_changed = on_hover_changed
        self._is_hovered = False

        self.setObjectName("legend-entry")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if self.spec.highlight_label is not None else Qt.CursorShape.ArrowCursor
        )

        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(6, 4, 6, 4)
        row_layout.setSpacing(8)

        swatch = QFrame()
        swatch.setFixedSize(14, 14)
        swatch.setFrameShape(QFrame.Shape.Box)
        swatch.setStyleSheet(f"background-color: {spec.color.name()}; border: 1px solid #101010;")
        swatch.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        label = QLabel(spec.text)
        label.setWordWrap(True)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        row_layout.addWidget(swatch)
        row_layout.addWidget(label, 1)
        self._apply_style()

    def enterEvent(self, event) -> None:  # noqa: ANN001
        if self.spec.highlight_label is not None:
            self._on_hover_changed(self.spec.highlight_label)
            self.set_hovered(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: ANN001
        if self.spec.highlight_label is not None:
            self._on_hover_changed(None)
            self.set_hovered(False)
        super().leaveEvent(event)

    def set_hovered(self, hovered: bool) -> None:
        if self._is_hovered == hovered:
            return
        self._is_hovered = hovered
        self._apply_style()

    def _apply_style(self) -> None:
        if self._is_hovered:
            self.setStyleSheet(
                "QFrame#legend-entry {"
                "background-color: rgba(111, 180, 255, 32);"
                "border: 1px solid rgba(111, 180, 255, 170);"
                "border-radius: 6px;"
                "}"
            )
            return

        self.setStyleSheet(
            "QFrame#legend-entry {"
            "background-color: transparent;"
            "border: 1px solid transparent;"
            "border-radius: 6px;"
            "}"
        )


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

        self.manifest_selector = QComboBox()
        self.manifest_selector.currentIndexChanged.connect(self._load_manifest_entry)
        self.manifest_selector.hide()

        self.generator_combo = QComboBox()
        for spec in self.generator_specs:
            self.generator_combo.addItem(spec.name, spec.name)
        self.generator_combo.currentIndexChanged.connect(self._sync_generation_option_controls)

        self.generate_width_spin = QSpinBox()
        self.generate_width_spin.setRange(1, 200)
        self.generate_width_spin.setValue(50)

        self.generate_height_spin = QSpinBox()
        self.generate_height_spin.setRange(1, 200)
        self.generate_height_spin.setValue(50)

        self.generate_seed_spin = QSpinBox()
        self.generate_seed_spin.setRange(0, 2**31 - 1)
        self.generate_seed_spin.setSpecialValueText("Random")
        self.generate_seed_spin.setValue(0)

        self.randomize_seed_button = QPushButton("Random")
        self.randomize_seed_button.clicked.connect(self._randomize_seed)

        self.generation_intro_label = QLabel(
            "Run the same offline generator used by the export helper and preview the result immediately."
        )
        self.generation_intro_label.setWordWrap(True)

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
        splitter.addWidget(self.view)
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
        self._apply_loaded_dump(dump, self._format_loaded_file_label(dump.path))

    def _load_dump_payload(self, payload: dict[str, object], source_label: str) -> None:
        dump = load_worldgen_payload(payload, path=Path("<generated>"))
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
            status_tip="Generate a new preview with the current settings.",
        )
        self.randomize_seed_action = self._create_action(
            "Random seed",
            self._randomize_seed,
            status_tip="Choose a fresh random seed for preview generation.",
        )
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
        layout.addWidget(self.generation_intro_label)

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
        form.addRow("Seed", seed_row)
        layout.addLayout(form)

        layout.addWidget(self.generator_options_note)
        layout.addLayout(self.generation_option_form)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.generation_progress_label)
        layout.addWidget(self.generation_progress_bar)
        return group

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

    def _current_generator_spec(self) -> OfflineGeneratorSpec:
        if not self.generator_specs:
            raise ValueError(self.generation_error or "Generator previews are unavailable in this environment.")
        return resolve_offline_generator(str(self.generator_combo.currentData()))

    def _sync_generation_option_controls(self) -> None:
        if not self.generator_specs:
            self.generator_combo.setEnabled(False)
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
        seed = self.generate_seed_spin.value() or generate_random_seed()

        request = PreviewGenerationRequest(
            generator_spec=generator_spec,
            width=width,
            height=height,
            seed=seed,
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

    def _on_generation_succeeded(self, dump_obj: object, source_label: str, seed: int) -> None:
        if not isinstance(dump_obj, WorldgenDump):
            self._on_generation_failed("The generated preview payload could not be loaded into the viewer.")
            return

        if self.generate_seed_spin.value() == 0:
            self.generate_seed_spin.setValue(seed)

        self.current_manifest_path = None
        self.manifest_entries = ()
        self._sync_manifest_selector()
        self._apply_loaded_dump(dump_obj, source_label)

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

        self.generate_button.setText("Generate preview")
        self.generation_progress_label.hide()
        self.generation_progress_bar.hide()
        self.randomize_seed_action.setEnabled(True)
        self.quit_action.setEnabled(True)
        self._sync_generation_option_controls()

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

        label_width = max(len(label) for label, _ in display_items + ([('Other categories', hidden_count)] if hidden_count else []))
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
            return f"Territory {record.territory_id}"

        if mode == "rivers":
            return _river_role_label(record)

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
            river_role = _river_role_label(record)
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
                entries.append(
                    LegendEntrySpec(
                        _stable_color(f"territory:{territory_id}", saturation=180, value=220),
                        f"Territory {territory_id}",
                        f"Territory {territory_id}",
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


def _hex_center(coord: HexCoord) -> QPointF:
    col, row = coord
    x = HEX_RADIUS * 1.5 * col
    y = HEX_RADIUS * SQRT3 * (row + 0.5 * (col & 1))
    return QPointF(x, y)


def _hex_polygon(coord: HexCoord) -> list[QPointF]:
    center = _hex_center(coord)
    points: list[QPointF] = []
    for angle in HEX_VERTEX_ANGLES:
        radians = math.radians(angle)
        points.append(QPointF(center.x() + HEX_RADIUS * math.cos(radians), center.y() + HEX_RADIUS * math.sin(radians)))
    return points


def _river_line(coord: HexCoord, side: str) -> tuple[QPointF, QPointF]:
    start_point, end_point = _edge_points_for_side(coord, side)
    inset = 0.18
    return (
        QPointF(
            start_point.x() + (end_point.x() - start_point.x()) * inset,
            start_point.y() + (end_point.y() - start_point.y()) * inset,
        ),
        QPointF(
            end_point.x() + (start_point.x() - end_point.x()) * inset,
            end_point.y() + (start_point.y() - end_point.y()) * inset,
        ),
    )


def _river_segment_key(coord: HexCoord, edge: dict[str, object], side: str) -> tuple[tuple[int, int], tuple[int, int]] | tuple[HexCoord, str]:
    between = edge.get("between")
    if isinstance(between, list) and len(between) == 2:
        first = _coord_from_between_value(between[0])
        second = _coord_from_between_value(between[1])
        if first is not None and second is not None:
            return tuple(sorted((first, second)))
    return coord, side


def _edge_points_for_side(coord: HexCoord, side: str) -> tuple[QPointF, QPointF]:
    polygon = _hex_polygon(coord)
    center = _hex_center(coord)
    neighbor_coord = _neighbor_coord_for_side(coord, side)
    if neighbor_coord is None:
        return polygon[0], polygon[1]

    neighbor_center = _hex_center(neighbor_coord)
    target_midpoint = QPointF((center.x() + neighbor_center.x()) / 2, (center.y() + neighbor_center.y()) / 2)

    best_index = 0
    best_distance = float("inf")
    for index, start_point in enumerate(polygon):
        end_point = polygon[(index + 1) % len(polygon)]
        midpoint = QPointF((start_point.x() + end_point.x()) / 2, (start_point.y() + end_point.y()) / 2)
        distance = (midpoint.x() - target_midpoint.x()) ** 2 + (midpoint.y() - target_midpoint.y()) ** 2
        if distance < best_distance:
            best_distance = distance
            best_index = index

    return polygon[best_index], polygon[(best_index + 1) % len(polygon)]


def _neighbor_coord_for_side(coord: HexCoord, side: str) -> HexCoord | None:
    col, row = coord
    odd_column = (col % 2) == 1

    if side == "east":
        return col, row + 1
    if side == "west":
        return col, row - 1
    if side == "north_west":
        return col - 1, row if odd_column else row - 1
    if side == "north_east":
        return col - 1, row + 1 if odd_column else row
    if side == "south_west":
        return col + 1, row if odd_column else row - 1
    if side == "south_east":
        return col + 1, row + 1 if odd_column else row
    return None


def _coord_from_between_value(value: object) -> HexCoord | None:
    if not isinstance(value, list | tuple) or len(value) != 2:
        return None
    first, second = value
    if not isinstance(first, int) or not isinstance(second, int):
        return None
    return first, second


def _stable_color(key: str, saturation: int = 130, value: int = 190) -> QColor:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    hue = int.from_bytes(digest[:2], "big") % 360
    return QColor.fromHsv(hue, saturation, value)


def _water_color_from_kind(kind: str) -> QColor:
    if kind == "coast":
        return QColor("#5aaed6")
    if kind == "lake":
        return QColor("#5d97c7")
    if kind == "sea_ice":
        return QColor("#dbeeff")
    return QColor("#2f507c")


def _water_color_for_record(record: HexRecord) -> QColor:
    terrain_key = (record.terrain or "").lower()
    if terrain_key == "coast" or record.is_coast_water:
        return _water_color_from_kind("coast")
    if terrain_key == "lake" or record.geoform_type == "lake":
        return _water_color_from_kind("lake")
    if terrain_key == "seaice":
        return _water_color_from_kind("sea_ice")
    return _water_color_from_kind("ocean")


def _overlay_water_label(record: HexRecord) -> str:
    terrain_key = (record.terrain or "").lower()
    if terrain_key == "seaice":
        return "Sea ice"
    if terrain_key == "lake" or record.geoform_type == "lake":
        return "Lake"
    if terrain_key == "coast" or record.is_coast_water:
        return "Coast / shallow water"
    return "Ocean / deep sea"


def _river_role_label(record: HexRecord) -> str:
    return river_role_label_for_record(record)


def _altitude_bucket_label(dump: WorldgenDump, record: HexRecord) -> str:
    low, high = dump.altitude_range
    sealevel = _heightmap_sealevel(dump)
    low_land = min(high, max(low, sealevel + 6.0))
    mid_land = (low_land + high) / 2 if high > low_land else high
    deep_water_cutoff = (low + sealevel) / 2
    high_land_cutoff = (mid_land + high) / 2 if high > mid_land else high

    if record.is_water:
        return "Deep water" if record.altitude <= deep_water_cutoff else "Shallow water"
    if record.altitude <= mid_land:
        return "Low land"
    if record.altitude <= high_land_cutoff:
        return "High land"
    return "Peaks"


def _moisture_bucket_label(dump: WorldgenDump, record: HexRecord) -> str:
    low, high = dump.moisture_range
    mid = (low + high) / 2
    dry_cutoff = (low + mid) / 2
    wet_cutoff = (mid + high) / 2

    if record.moisture <= dry_cutoff:
        return "Dry"
    if record.moisture <= wet_cutoff:
        return "Balanced"
    return "Wet"


def _title_from_identifier(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").strip().title()


def _runtime_terrain_key(dump: WorldgenDump, record: HexRecord) -> str | None:
    runtime_tile = dump.runtime_tiles_by_coord.get(record.coord)
    terrain_value = runtime_tile.get("terrain") if runtime_tile is not None else None
    if isinstance(terrain_value, str) and terrain_value:
        return terrain_value
    return record.terrain


def _runtime_resource_key(dump: WorldgenDump, record: HexRecord) -> str | None:
    runtime_tile = dump.runtime_tiles_by_coord.get(record.coord)
    resource_value = runtime_tile.get("resource") if runtime_tile is not None else None
    return str(resource_value) if isinstance(resource_value, str) and resource_value else None


def _resource_label(dump: WorldgenDump, record: HexRecord) -> str:
    if not record.visible_in_runtime:
        return "Outside runtime bounds"

    resource_key = _runtime_resource_key(dump, record)
    if resource_key is None:
        return "No resource"

    return resource_display_text(resource_key) or resource_key


def _resource_color(dump: WorldgenDump, record: HexRecord) -> QColor:
    label = _resource_label(dump, record)
    special_color = RESOURCE_SPECIAL_COLORS.get(label)
    if special_color is not None:
        return QColor(special_color)

    resource_key = _runtime_resource_key(dump, record)
    return _stable_color(f"resource:{resource_key or label}", saturation=160, value=220)


def _runtime_terrain_label(dump: WorldgenDump, record: HexRecord) -> str:
    terrain_key = _runtime_terrain_key(dump, record)
    if terrain_key is None:
        if record.is_water:
            terrain_key = record.terrain or ""
            lowered = terrain_key.strip().lower().replace("_", "").replace("-", "")
            if lowered == "seaice":
                return "Sea ice / ice water"
            if lowered == "lake" or record.geoform_type == "lake":
                return "Lake"
            if lowered == "coast" or record.is_coast_water:
                return "Coast"
            return "Sea / ocean"
        return record.biome_title

    lowered = terrain_key.strip().lower().replace("_", "").replace("-", "")
    if lowered in {"sea", "ocean"}:
        return "Sea / ocean"
    if lowered == "seaice":
        return "Sea ice / ice water"

    return terrain_display_name(terrain_key) or _title_from_identifier(terrain_key)


def _runtime_terrain_color(dump: WorldgenDump, record: HexRecord) -> QColor:
    terrain_key = _runtime_terrain_key(dump, record)
    if terrain_key is None:
        return _water_color_for_record(record) if record.is_water else QColor(
            BIOME_COLORS.get(record.biome_key, _stable_color(record.biome_key))
        )

    lowered = terrain_key.strip().lower().replace("_", "").replace("-", "")
    if lowered == "coast":
        return QColor(TERRAIN_COLORS["coast"])
    if lowered == "lake":
        return QColor(TERRAIN_COLORS["lake"])
    if lowered == "seaice":
        return QColor(TERRAIN_COLORS["sea_ice"])
    if record.is_water or lowered in {"sea", "ocean"}:
        return QColor(TERRAIN_COLORS["ocean"])
    if "volcano" in lowered:
        return QColor(TERRAIN_COLORS["volcano"])

    land_color = _runtime_terrain_land_color(lowered, record)
    if "mountain" in lowered:
        return _blend(QColor(TERRAIN_COLORS["mountains"]), land_color, 0.36) if land_color is not None else QColor(
            TERRAIN_COLORS["mountains"]
        )
    if "hill" in lowered:
        return _blend(QColor(TERRAIN_COLORS["hills"]), land_color, 0.48) if land_color is not None else QColor(
            TERRAIN_COLORS["hills"]
        )
    if land_color is not None:
        return land_color

    return QColor(_stable_color(lowered))


def _runtime_terrain_land_color(lowered: str, record: HexRecord) -> QColor | None:
    if "ice" in lowered or "snow" in lowered:
        return QColor(TERRAIN_COLORS["snow"])
    if "tundra" in lowered:
        return QColor(TERRAIN_COLORS["tundra"])
    if "desert" in lowered:
        return QColor(TERRAIN_COLORS["desert"])
    if "jungle" in lowered:
        return QColor(TERRAIN_COLORS["jungle"])
    if "pineforest" in lowered or "heavyforest" in lowered or "forest" in lowered:
        return QColor(TERRAIN_COLORS["forest"])
    if "grass" in lowered:
        return QColor(TERRAIN_COLORS["grasslands"])
    if "savanna" in lowered:
        return QColor(TERRAIN_COLORS["savannah"])
    if "scrub" in lowered:
        return QColor(TERRAIN_COLORS["scrubland"])
    if "plain" in lowered:
        return QColor(TERRAIN_COLORS["plains"])

    biome_color = BIOME_COLORS.get(record.biome_key)
    return QColor(biome_color) if biome_color is not None else None


def _altitude_color(value: float, bounds: tuple[float, float], is_water: bool) -> QColor:
    low, high = bounds
    if high <= low:
        return QColor("#4c7aa8") if is_water else QColor("#7da261")

    normalized = max(0.0, min(1.0, (value - low) / (high - low)))
    if is_water:
        return _blend(QColor("#16314f"), QColor("#5ea3d4"), normalized)
    if normalized < 0.55:
        return _blend(QColor("#6c9b54"), QColor("#9f855c"), normalized / 0.55)
    return _blend(QColor("#9f855c"), QColor("#dfe5ea"), (normalized - 0.55) / 0.45)


def _moisture_color(value: float, bounds: tuple[float, float]) -> QColor:
    low, high = bounds
    if high <= low:
        return QColor("#7aa86a")

    normalized = max(0.0, min(1.0, (value - low) / (high - low)))
    if normalized < 0.5:
        return _blend(QColor("#c8a86a"), QColor("#6faa62"), normalized / 0.5)
    return _blend(QColor("#6faa62"), QColor("#4aa0c8"), (normalized - 0.5) / 0.5)


def _blend(first: QColor, second: QColor, amount: float) -> QColor:
    clamped = max(0.0, min(1.0, amount))
    red = round(first.red() + (second.red() - first.red()) * clamped)
    green = round(first.green() + (second.green() - first.green()) * clamped)
    blue = round(first.blue() + (second.blue() - first.blue()) * clamped)
    return QColor(red, green, blue)


def _heightmap_sealevel(dump: WorldgenDump) -> float:
    raw_payload = dump.raw_payload.get("raw") if isinstance(dump.raw_payload.get("raw"), dict) else {}
    heightmap = raw_payload.get("heightmap") if isinstance(raw_payload.get("heightmap"), dict) else {}
    sealevel = heightmap.get("sealevel")
    if isinstance(sealevel, int | float):
        return float(sealevel)

    low, high = dump.altitude_range
    return (low + high) / 2


if __name__ == "__main__":
    raise SystemExit(main())

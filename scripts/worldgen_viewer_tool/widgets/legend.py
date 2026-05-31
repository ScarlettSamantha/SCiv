"""Legend widgets for the standalone worldgen viewer."""

from dataclasses import dataclass
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel


@dataclass(frozen=True, slots=True)
class LegendEntrySpec:
    color: QColor
    text: str
    highlight_label: str | None


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

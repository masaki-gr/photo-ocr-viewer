from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable, List, Optional

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QAction, QColor, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsPixmapItem,
    QGraphicsPolygonItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .image_store import list_supported_images
from .ocr import OCREngine, OCRLine


class ClickablePolygonItem(QGraphicsPolygonItem):
    def __init__(self, index: int, polygon: QPolygonF, on_click: Callable[[int], None]) -> None:
        super().__init__(polygon)
        self.index = index
        self._on_click = on_click
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self._on_click(self.index)
        super().mousePressEvent(event)


class ImageView(QGraphicsView):
    boxClicked = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._box_items: List[ClickablePolygonItem] = []
        self._selected_index: Optional[int] = None

        self._normal_pen = QPen(QColor(80, 180, 255, 160), 2)
        self._selected_pen = QPen(QColor(255, 110, 0, 220), 3)
        self._normal_brush = QColor(80, 180, 255, 40)
        self._selected_brush = QColor(255, 110, 0, 70)

    def set_image(self, image_path: str) -> None:
        pixmap_item = QGraphicsPixmapItem(QPixmap(image_path))
        if pixmap_item.pixmap().isNull():
            raise ValueError(f"Failed to load image: {image_path}")

        self.scene.clear()
        self._box_items.clear()
        self._selected_index = None

        self._pixmap_item = pixmap_item
        self.scene.addItem(self._pixmap_item)
        self.scene.setSceneRect(self._pixmap_item.boundingRect())
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def show_ocr_boxes(self, lines: List[OCRLine]) -> None:
        for item in self._box_items:
            self.scene.removeItem(item)
        self._box_items.clear()

        for idx, line in enumerate(lines):
            polygon = QPolygonF([QPointF(x, y) for x, y in line.points])
            item = ClickablePolygonItem(idx, polygon, self.boxClicked.emit)
            item.setPen(self._normal_pen)
            item.setBrush(self._normal_brush)
            self.scene.addItem(item)
            self._box_items.append(item)

    def select_box(self, index: Optional[int]) -> None:
        self._selected_index = index
        for idx, item in enumerate(self._box_items):
            if index is not None and idx == index:
                item.setPen(self._selected_pen)
                item.setBrush(self._selected_brush)
            else:
                item.setPen(self._normal_pen)
                item.setBrush(self._normal_brush)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if self._pixmap_item is not None:
            self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Photo OCR Viewer")
        self.resize(1320, 820)

        self.ocr_engine = OCREngine(lang="japan")
        self.current_folder: Optional[Path] = None
        self.image_paths: List[Path] = []
        self.current_index: int = -1
        self.current_lines: List[OCRLine] = []

        self.image_view = ImageView()
        self.image_view.boxClicked.connect(self.on_box_clicked)

        self.lines_list = QListWidget()
        self.lines_list.currentRowChanged.connect(self.on_line_selected)

        self.full_text_panel = QTextEdit()
        self.full_text_panel.setReadOnly(True)

        self.selected_label = QLabel("Selected line: (none)")
        self.selected_label.setWordWrap(True)

        self.copy_selected_button = QPushButton("Copy Selected")
        self.copy_selected_button.clicked.connect(self.copy_selected_line)

        self.copy_all_button = QPushButton("Copy Full Text")
        self.copy_all_button.clicked.connect(self.copy_full_text)

        self.status_label = QLabel("Open a folder to start.")

        self._build_layout()
        self._build_toolbar()

    def _build_layout(self) -> None:
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("Full OCR Text"))
        right_layout.addWidget(self.full_text_panel)
        right_layout.addWidget(QLabel("OCR Lines"))
        right_layout.addWidget(self.lines_list)
        right_layout.addWidget(self.selected_label)
        right_layout.addWidget(self.copy_selected_button)
        right_layout.addWidget(self.copy_all_button)
        right_layout.addWidget(self.status_label)

        splitter = QSplitter()
        splitter.addWidget(self.image_view)
        splitter.addWidget(right_panel)
        splitter.setSizes([900, 420])

        container = QWidget()
        root_layout = QHBoxLayout(container)
        root_layout.addWidget(splitter)
        self.setCentralWidget(container)

    def _build_toolbar(self) -> None:
        toolbar = self.addToolBar("Main")

        open_action = QAction("Open Folder", self)
        open_action.triggered.connect(self.open_folder)
        toolbar.addAction(open_action)

        self.prev_action = QAction("Previous", self)
        self.prev_action.triggered.connect(self.show_previous_image)
        toolbar.addAction(self.prev_action)

        self.next_action = QAction("Next", self)
        self.next_action.triggered.connect(self.show_next_image)
        toolbar.addAction(self.next_action)

        rerun_action = QAction("Re-run OCR", self)
        rerun_action.triggered.connect(lambda: self.run_ocr(force=True))
        toolbar.addAction(rerun_action)

        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy_selected_line)
        toolbar.addAction(copy_action)

        self._refresh_nav_actions()

    def open_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select image folder")
        if not path:
            return

        folder = Path(path)
        try:
            images = list_supported_images(folder)
        except NotADirectoryError as exc:
            QMessageBox.critical(self, "Invalid folder", str(exc))
            return

        if not images:
            QMessageBox.warning(self, "No images", "No png/jpg/jpeg files found in this folder.")
            return

        self.current_folder = folder
        self.image_paths = images
        self.current_index = 0
        self.show_current_image()

    def show_current_image(self) -> None:
        if not (0 <= self.current_index < len(self.image_paths)):
            return

        image_path = self.image_paths[self.current_index]
        self.status_label.setText(f"Image: {image_path.name}")

        try:
            self.image_view.set_image(str(image_path))
        except ValueError as exc:
            QMessageBox.critical(self, "Load error", str(exc))
            return

        self.run_ocr(force=False)
        self._refresh_nav_actions()

    def run_ocr(self, force: bool = False) -> None:
        if not (0 <= self.current_index < len(self.image_paths)):
            return

        image_path = str(self.image_paths[self.current_index])
        if force:
            self.ocr_engine.clear_cache_for(image_path)

        self.status_label.setText(f"Running OCR: {os.path.basename(image_path)}")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.current_lines = self.ocr_engine.recognize(image_path, force=force)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "OCR error", str(exc))
            self.current_lines = []
        finally:
            QApplication.restoreOverrideCursor()

        self._refresh_ocr_ui()

    def _refresh_ocr_ui(self) -> None:
        self.image_view.show_ocr_boxes(self.current_lines)

        self.lines_list.clear()
        for line in self.current_lines:
            item = QListWidgetItem(line.text)
            self.lines_list.addItem(item)

        full_text = "\n".join([line.text for line in self.current_lines])
        self.full_text_panel.setPlainText(full_text)

        if self.current_lines:
            self.lines_list.setCurrentRow(0)
        else:
            self.selected_label.setText("Selected line: (none)")
            self.image_view.select_box(None)
            self.status_label.setText("OCR complete: no text found")

    def on_box_clicked(self, index: int) -> None:
        if 0 <= index < self.lines_list.count():
            self.lines_list.setCurrentRow(index)

    def on_line_selected(self, index: int) -> None:
        if 0 <= index < len(self.current_lines):
            text = self.current_lines[index].text
            self.selected_label.setText(f"Selected line: {text}")
            self.image_view.select_box(index)
            self.status_label.setText(f"OCR complete: line {index + 1}/{len(self.current_lines)} selected")
        else:
            self.selected_label.setText("Selected line: (none)")
            self.image_view.select_box(None)

    def copy_selected_line(self) -> None:
        idx = self.lines_list.currentRow()
        if 0 <= idx < len(self.current_lines):
            QApplication.clipboard().setText(self.current_lines[idx].text)
            self.status_label.setText("Copied selected line")

    def copy_full_text(self) -> None:
        QApplication.clipboard().setText(self.full_text_panel.toPlainText())
        self.status_label.setText("Copied full text")

    def show_previous_image(self) -> None:
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()

    def show_next_image(self) -> None:
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.show_current_image()

    def _refresh_nav_actions(self) -> None:
        has_images = len(self.image_paths) > 0
        self.prev_action.setEnabled(has_images and self.current_index > 0)
        self.next_action.setEnabled(has_images and self.current_index < len(self.image_paths) - 1)


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

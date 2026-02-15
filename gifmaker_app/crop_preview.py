import numpy as np
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class CropPreviewWidget(QWidget):
    cropChanged = Signal(int, int, int, int)

    HANDLE_RADIUS = 7
    MIN_SIZE = 4
    VIEW_MARGIN = 12

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(360)
        self.setMouseTracking(True)

        self._image_pixmap: QPixmap | None = None
        self._source_width = 0
        self._source_height = 0

        self._crop_x = 0
        self._crop_y = 0
        self._crop_w = 0
        self._crop_h = 0

        self._drag_corner: str | None = None
        self._dragging_rect = False
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self._hover_corner: str | None = None
        self._hover_inside = False

    def set_source_size(self, width: int, height: int) -> None:
        self._source_width = max(1, width)
        self._source_height = max(1, height)
        self.set_crop_rect(0, 0, self._source_width, self._source_height, emit_signal=True)

    def set_frame(self, rgb: np.ndarray) -> None:
        h, w, _ = rgb.shape
        bytes_per_line = 3 * w
        image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
        self._image_pixmap = QPixmap.fromImage(image)
        if self._source_width == 0 or self._source_height == 0:
            self.set_source_size(w, h)
        self.update()

    def crop_rect(self) -> tuple[int, int, int, int] | None:
        if self._source_width <= 0 or self._source_height <= 0:
            return None
        return (self._crop_x, self._crop_y, self._crop_w, self._crop_h)

    def set_crop_rect(self, x: int, y: int, width: int, height: int, emit_signal: bool = False) -> None:
        if self._source_width <= 0 or self._source_height <= 0:
            return

        x = max(0, min(x, self._source_width - 1))
        y = max(0, min(y, self._source_height - 1))
        width = max(self.MIN_SIZE, min(width, self._source_width - x))
        height = max(self.MIN_SIZE, min(height, self._source_height - y))

        changed = (
            x != self._crop_x
            or y != self._crop_y
            or width != self._crop_w
            or height != self._crop_h
        )

        self._crop_x = x
        self._crop_y = y
        self._crop_w = width
        self._crop_h = height
        self.update()

        if changed and emit_signal:
            self.cropChanged.emit(self._crop_x, self._crop_y, self._crop_w, self._crop_h)

    def _display_image_rect(self) -> tuple[float, float, float, float, float] | None:
        if self._image_pixmap is None:
            return None

        iw = self._image_pixmap.width()
        ih = self._image_pixmap.height()
        if iw <= 0 or ih <= 0:
            return None

        avail_w = max(1.0, float(self.width() - 2 * self.VIEW_MARGIN))
        avail_h = max(1.0, float(self.height() - 2 * self.VIEW_MARGIN))
        scale = min(avail_w / iw, avail_h / ih)
        draw_w = iw * scale
        draw_h = ih * scale
        left = self.VIEW_MARGIN + (avail_w - draw_w) / 2.0
        top = self.VIEW_MARGIN + (avail_h - draw_h) / 2.0
        return left, top, draw_w, draw_h, scale

    def _source_to_widget(self, sx: float, sy: float) -> QPointF:
        image_rect = self._display_image_rect()
        if image_rect is None:
            return QPointF(0, 0)

        left, top, _, _, scale = image_rect
        return QPointF(left + sx * scale, top + sy * scale)

    def _widget_to_source(self, wx: float, wy: float) -> tuple[float, float]:
        image_rect = self._display_image_rect()
        if image_rect is None:
            return 0.0, 0.0

        left, top, draw_w, draw_h, _ = image_rect
        rx = 0.0 if draw_w <= 1 else (wx - left) / draw_w
        ry = 0.0 if draw_h <= 1 else (wy - top) / draw_h
        rx = max(0.0, min(1.0, rx))
        ry = max(0.0, min(1.0, ry))

        sx = rx * self._source_width
        sy = ry * self._source_height
        return sx, sy

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#111"))

        if self._image_pixmap is None:
            painter.setPen(QColor("#ddd"))
            painter.drawText(self.rect(), Qt.AlignCenter, "Open a video to begin")
            return

        image_rect = self._display_image_rect()
        if image_rect is None:
            return

        left, top, draw_w, draw_h, _ = image_rect
        painter.drawPixmap(int(left), int(top), int(draw_w), int(draw_h), self._image_pixmap)

        if self._crop_w <= 0 or self._crop_h <= 0:
            return

        p1 = self._source_to_widget(self._crop_x, self._crop_y)
        p2 = self._source_to_widget(self._crop_x + self._crop_w, self._crop_y + self._crop_h)

        rect_left = min(p1.x(), p2.x())
        rect_top = min(p1.y(), p2.y())
        rect_w = abs(p2.x() - p1.x())
        rect_h = abs(p2.y() - p1.y())

        painter.setPen(QPen(QColor("#22c55e"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect_left, rect_top, rect_w, rect_h)

        painter.setPen(Qt.NoPen)
        corners = (
            ("tl", rect_left, rect_top),
            ("tr", rect_left + rect_w, rect_top),
            ("bl", rect_left, rect_top + rect_h),
            ("br", rect_left + rect_w, rect_top + rect_h),
        )
        for name, cx, cy in corners:
            if name == self._drag_corner:
                painter.setBrush(QColor("#86efac"))
            elif name == self._hover_corner:
                painter.setBrush(QColor("#4ade80"))
            else:
                painter.setBrush(QColor("#22c55e"))
            painter.drawEllipse(QPointF(cx, cy), self.HANDLE_RADIUS, self.HANDLE_RADIUS)

    def _hit_test(self, mouse_pos: QPointF) -> tuple[str | None, bool]:
        corners = {
            "tl": self._source_to_widget(self._crop_x, self._crop_y),
            "tr": self._source_to_widget(self._crop_x + self._crop_w, self._crop_y),
            "bl": self._source_to_widget(self._crop_x, self._crop_y + self._crop_h),
            "br": self._source_to_widget(self._crop_x + self._crop_w, self._crop_y + self._crop_h),
        }

        for name, point in corners.items():
            if (mouse_pos - point).manhattanLength() <= self.HANDLE_RADIUS * 2:
                return name, False

        sx, sy = self._widget_to_source(mouse_pos.x(), mouse_pos.y())
        inside = self._crop_x <= sx <= self._crop_x + self._crop_w and self._crop_y <= sy <= self._crop_y + self._crop_h
        return None, inside

    def _update_cursor_and_hover(self, mouse_pos: QPointF) -> None:
        corner, inside = self._hit_test(mouse_pos)
        self._hover_corner = corner
        self._hover_inside = inside

        if corner in ("tl", "br"):
            self.setCursor(Qt.SizeFDiagCursor)
        elif corner in ("tr", "bl"):
            self.setCursor(Qt.SizeBDiagCursor)
        elif inside:
            self.setCursor(Qt.SizeAllCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.LeftButton or self._image_pixmap is None:
            return

        self._drag_corner = None
        self._dragging_rect = False

        mouse_pos = event.position()
        corner, inside = self._hit_test(mouse_pos)
        if corner is not None:
            self._drag_corner = corner
            self.update()
            return

        sx, sy = self._widget_to_source(mouse_pos.x(), mouse_pos.y())
        if inside:
            self._dragging_rect = True
            self._drag_offset_x = int(sx) - self._crop_x
            self._drag_offset_y = int(sy) - self._crop_y
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_corner is None and not self._dragging_rect:
            self._update_cursor_and_hover(event.position())
            return

        sx, sy = self._widget_to_source(event.position().x(), event.position().y())

        if self._dragging_rect:
            new_x = int(sx) - self._drag_offset_x
            new_y = int(sy) - self._drag_offset_y
            new_x = max(0, min(new_x, self._source_width - self._crop_w))
            new_y = max(0, min(new_y, self._source_height - self._crop_h))
            self.set_crop_rect(new_x, new_y, self._crop_w, self._crop_h, emit_signal=True)
            return

        left = self._crop_x
        top = self._crop_y
        right = self._crop_x + self._crop_w
        bottom = self._crop_y + self._crop_h

        if self._drag_corner == "tl":
            left = min(int(sx), right - self.MIN_SIZE)
            top = min(int(sy), bottom - self.MIN_SIZE)
        elif self._drag_corner == "tr":
            right = max(int(sx), left + self.MIN_SIZE)
            top = min(int(sy), bottom - self.MIN_SIZE)
        elif self._drag_corner == "bl":
            left = min(int(sx), right - self.MIN_SIZE)
            bottom = max(int(sy), top + self.MIN_SIZE)
        elif self._drag_corner == "br":
            right = max(int(sx), left + self.MIN_SIZE)
            bottom = max(int(sy), top + self.MIN_SIZE)

        left = max(0, min(left, self._source_width - self.MIN_SIZE))
        top = max(0, min(top, self._source_height - self.MIN_SIZE))
        right = max(left + self.MIN_SIZE, min(right, self._source_width))
        bottom = max(top + self.MIN_SIZE, min(bottom, self._source_height))

        self.set_crop_rect(left, top, right - left, bottom - top, emit_signal=True)

    def mouseReleaseEvent(self, event) -> None:
        mouse_pos = event.position()
        self._drag_corner = None
        self._dragging_rect = False
        self._update_cursor_and_hover(mouse_pos)

    def leaveEvent(self, event) -> None:
        del event
        self._hover_corner = None
        self._hover_inside = False
        self.setCursor(Qt.ArrowCursor)
        self.update()

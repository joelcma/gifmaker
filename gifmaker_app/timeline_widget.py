from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QSizePolicy, QWidget


class TimelineWidget(QWidget):
    currentFrameChanged = Signal(int)
    rangeChanged = Signal(int, int)

    HANDLE_RADIUS = 7
    KNOB_RADIUS = 6
    PADDING = 10

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(110)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMouseTracking(True)

        self.frame_count = 1
        self.current_frame = 0
        self.start_frame = 0
        self.end_frame = 0
        self.thumbnails: list[QPixmap] = []

        self._dragging: str | None = None

    def set_video_data(
        self,
        frame_count: int,
        start_frame: int,
        end_frame: int,
        current_frame: int,
        thumbnails: list[QPixmap],
    ) -> None:
        self.frame_count = max(frame_count, 1)
        self.start_frame = max(0, min(start_frame, self.frame_count - 1))
        self.end_frame = max(self.start_frame, min(end_frame, self.frame_count - 1))
        self.current_frame = max(0, min(current_frame, self.frame_count - 1))
        self.thumbnails = thumbnails
        self.update()

    def set_current_frame(self, frame: int) -> None:
        frame = max(0, min(frame, self.frame_count - 1))
        if frame != self.current_frame:
            self.current_frame = frame
            self.update()

    def set_range(self, start: int, end: int) -> None:
        start = max(0, min(start, self.frame_count - 1))
        end = max(start, min(end, self.frame_count - 1))
        changed = (start != self.start_frame) or (end != self.end_frame)
        self.start_frame = start
        self.end_frame = end
        if changed:
            self.rangeChanged.emit(start, end)
        self.update()

    def _frame_to_x(self, frame: int) -> int:
        timeline = self._timeline_rect()
        if self.frame_count <= 1:
            return timeline.left()
        width = max(1, timeline.width() - 1)
        return timeline.left() + int((frame / (self.frame_count - 1)) * width)

    def _x_to_frame(self, x: int) -> int:
        timeline = self._timeline_rect()
        if self.frame_count <= 1:
            return 0
        width = max(1, timeline.width() - 1)
        pos = max(timeline.left(), min(x, timeline.right())) - timeline.left()
        return int(round((pos / width) * (self.frame_count - 1)))

    def _timeline_rect(self):
        return self.rect().adjusted(self.PADDING, self.PADDING, -self.PADDING, -self.PADDING)

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        timeline = self._timeline_rect()
        painter.fillRect(timeline, QColor("#1f1f1f"))

        if self.thumbnails:
            thumb_width = timeline.width() / len(self.thumbnails)
            for index, pixmap in enumerate(self.thumbnails):
                x = int(timeline.left() + index * thumb_width)
                w = int(thumb_width + 1)
                target = timeline.adjusted(x - timeline.left(), 0, -(timeline.right() - (x + w)), 0)
                painter.drawPixmap(target, pixmap)

        start_x = self._frame_to_x(self.start_frame)
        end_x = self._frame_to_x(self.end_frame)

        overlay = QColor(0, 0, 0, 120)
        painter.fillRect(timeline.left(), timeline.top(), max(0, start_x - timeline.left()), timeline.height(), overlay)
        painter.fillRect(end_x, timeline.top(), max(0, timeline.right() - end_x), timeline.height(), overlay)

        current_x = self._frame_to_x(self.current_frame)
        painter.setPen(QPen(QColor("#f7d154"), 2))
        painter.drawLine(current_x, timeline.top(), current_x, timeline.bottom())

        painter.setPen(QPen(QColor("#22c55e"), 3))
        painter.drawLine(start_x, timeline.top(), start_x, timeline.bottom())
        painter.setBrush(QColor("#22c55e"))
        painter.setPen(QPen(QColor("#111111"), 1))
        painter.drawEllipse(start_x - self.KNOB_RADIUS, timeline.top() - self.KNOB_RADIUS, self.KNOB_RADIUS * 2, self.KNOB_RADIUS * 2)
        painter.drawEllipse(
            start_x - self.KNOB_RADIUS,
            timeline.bottom() - self.KNOB_RADIUS,
            self.KNOB_RADIUS * 2,
            self.KNOB_RADIUS * 2,
        )

        painter.setPen(QPen(QColor("#ef4444"), 3))
        painter.drawLine(end_x, timeline.top(), end_x, timeline.bottom())
        painter.setBrush(QColor("#ef4444"))
        painter.setPen(QPen(QColor("#111111"), 1))
        painter.drawEllipse(end_x - self.KNOB_RADIUS, timeline.top() - self.KNOB_RADIUS, self.KNOB_RADIUS * 2, self.KNOB_RADIUS * 2)
        painter.drawEllipse(
            end_x - self.KNOB_RADIUS,
            timeline.bottom() - self.KNOB_RADIUS,
            self.KNOB_RADIUS * 2,
            self.KNOB_RADIUS * 2,
        )

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return

        x = int(event.position().x())
        start_x = self._frame_to_x(self.start_frame)
        end_x = self._frame_to_x(self.end_frame)

        if abs(x - start_x) <= self.HANDLE_RADIUS:
            self._dragging = "start"
        elif abs(x - end_x) <= self.HANDLE_RADIUS:
            self._dragging = "end"
        else:
            self._dragging = "current"
            frame = self._x_to_frame(x)
            self.current_frame = frame
            self.currentFrameChanged.emit(frame)
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._dragging is None:
            return

        x = int(event.position().x())
        frame = self._x_to_frame(x)

        if self._dragging == "start":
            self.set_range(min(frame, self.end_frame), self.end_frame)
        elif self._dragging == "end":
            self.set_range(self.start_frame, max(frame, self.start_frame))
        elif self._dragging == "current":
            if frame != self.current_frame:
                self.current_frame = frame
                self.currentFrameChanged.emit(frame)
                self.update()

    def mouseReleaseEvent(self, event) -> None:
        del event
        self._dragging = None

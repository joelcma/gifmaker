import cv2
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QCheckBox,
    QFrame,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressDialog,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .crop_preview import CropPreviewWidget
from .timeline_widget import TimelineWidget
from .video_reader import VideoReader


class GifMakerWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GIF Maker")
        self.resize(980, 680)
        self.setStyleSheet(
            """
            QLineEdit, QComboBox, QPushButton {
                border-radius: 8px;
                padding: 4px 8px;
            }
            QPushButton {
                min-height: 28px;
            }
            QPushButton#openButton {
                background-color: #2b2b2b;
                color: #e5e5e5;
                border: 1px solid #4a4a4a;
                padding: 5px 12px;
                font-weight: 500;
            }
            QPushButton#openButton:hover {
                background-color: #363636;
            }
            QPushButton#openButton:pressed {
                background-color: #202020;
            }
            QPushButton#exportButton {
                background-color: #22c55e;
                color: #0b2214;
                border: 1px solid #16a34a;
                font-weight: 600;
                padding: 5px 12px;
            }
            QPushButton#exportButton:hover {
                background-color: #34d399;
            }
            QPushButton#exportButton:pressed {
                background-color: #16a34a;
            }
            QPushButton#exportButton:disabled {
                background-color: #2b2b2b;
                color: #8b8b8b;
                border: 1px solid #3a3a3a;
            }
            """
        )

        self.reader = VideoReader()
        self.current_frame = 0
        self.start_frame = 0
        self.end_frame = 0

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        self.open_button = QPushButton("Open Video")
        self.open_button.setObjectName("openButton")
        self.export_button = QPushButton("Export")
        self.export_button.setObjectName("exportButton")
        self.export_button.setEnabled(False)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["gif", "webm", "mp4", "mpeg"])
        self.format_combo.setCurrentText("gif")
        self.format_combo.setFixedWidth(110)
        self.compare_toggle = QCheckBox("Enable first/last comparison")
        self.compare_toggle.setEnabled(False)
        top_row.addWidget(self.open_button)
        top_row.addStretch(1)
        top_row.addWidget(self.compare_toggle)
        layout.addLayout(top_row)

        preview_row = QHBoxLayout()

        self.preview = CropPreviewWidget()
        self.preview.setStyleSheet("background-color: #111; color: #ddd; border: 1px solid #444;")
        preview_row.addWidget(self.preview, 3)

        self.comparison_preview = QLabel("Comparison disabled")
        self.comparison_preview.setAlignment(Qt.AlignCenter)
        self.comparison_preview.setMinimumHeight(360)
        self.comparison_preview.setMinimumWidth(300)
        self.comparison_preview.setStyleSheet("background-color: #111; color: #ddd; border: 1px solid #444;")
        self.comparison_preview.hide()
        preview_row.addWidget(self.comparison_preview, 2)

        layout.addLayout(preview_row)

        self.timeline = TimelineWidget()
        layout.addWidget(self.timeline)

        self.gif_width_spin = QSpinBox()
        self.gif_width_spin.setRange(120, 1920)
        self.gif_width_spin.setValue(480)
        self.gif_width_spin.setFixedWidth(92)
        self.gif_fps_spin = QSpinBox()
        self.gif_fps_spin.setRange(1, 30)
        self.gif_fps_spin.setValue(12)
        self.gif_fps_spin.setFixedWidth(86)
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(80)
        self.quality_spin.setFixedWidth(86)

        footer = QFrame()
        footer.setFrameShape(QFrame.StyledPanel)
        footer.setStyleSheet("QFrame { border: none; background-color: #161616; }")
        footer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(10, 8, 10, 8)
        footer_layout.setSpacing(8)

        footer_layout.addWidget(QLabel("Width"))
        footer_layout.addWidget(self.gif_width_spin)
        footer_layout.addSpacing(12)
        footer_layout.addWidget(QLabel("FPS"))
        footer_layout.addWidget(self.gif_fps_spin)
        footer_layout.addSpacing(12)
        footer_layout.addWidget(QLabel("Quality %"))
        footer_layout.addWidget(self.quality_spin)

        footer_layout.addStretch(1)
        footer_layout.addWidget(self.format_combo)
        footer_layout.addSpacing(10)
        self.size_estimate_label = QLabel("Est size: —")
        self.size_estimate_label.setStyleSheet("color: #cfcfcf;")
        footer_layout.addWidget(self.size_estimate_label)
        footer_layout.addWidget(self.export_button)
        layout.addWidget(footer)

        self.open_button.clicked.connect(self.open_video)
        self.export_button.clicked.connect(self.export_media)
        self.compare_toggle.toggled.connect(self.on_compare_toggled)
        self.timeline.currentFrameChanged.connect(self.on_timeline_current_changed)
        self.timeline.rangeChanged.connect(self.on_timeline_range_changed)
        self.preview.cropChanged.connect(self.on_crop_changed)
        self.gif_width_spin.valueChanged.connect(self.on_export_settings_changed)
        self.gif_fps_spin.valueChanged.connect(self.on_export_settings_changed)
        self.quality_spin.valueChanged.connect(self.on_export_settings_changed)
        self.format_combo.currentTextChanged.connect(self.on_export_format_changed)

    def closeEvent(self, event) -> None:
        self.reader.close()
        super().closeEvent(event)

    def open_video(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video",
            "",
            "Video files (*.mp4 *.mov *.mkv *.avi *.webm *.m4v);;All files (*)",
        )
        if not file_path:
            return

        self.load_video(file_path)

    def load_video(self, file_path: str) -> None:
        if not file_path:
            return

        try:
            info = self.reader.open(file_path)
        except Exception as exc:
            QMessageBox.critical(self, "Open failed", str(exc))
            return

        self.current_frame = 0
        self.start_frame = 0
        self.end_frame = info.frame_count - 1

        self.export_button.setEnabled(True)
        self.compare_toggle.setEnabled(True)

        self.gif_width_spin.setValue(min(480, info.width))

        self.preview.set_source_size(info.width, info.height)

        thumbnails = self._build_thumbnails(target_count=24, thumb_height=80)
        self.timeline.set_video_data(
            frame_count=info.frame_count,
            start_frame=self.start_frame,
            end_frame=self.end_frame,
            current_frame=self.current_frame,
            thumbnails=thumbnails,
        )

        self._show_frame(self.current_frame)
        self._update_comparison_view()
        self._update_size_estimate()

    def _build_thumbnails(self, target_count: int, thumb_height: int) -> list[QPixmap]:
        info = self.reader.info
        if info is None:
            return []

        count = max(2, min(target_count, info.frame_count))
        indices = np.linspace(0, info.frame_count - 1, num=count, dtype=np.int32)
        pixmaps: list[QPixmap] = []

        for frame_idx in indices:
            rgb = self.reader.read_frame_rgb(int(frame_idx))
            h, w, _ = rgb.shape
            thumb_width = max(1, int(w * (thumb_height / h)))
            resized = cv2.resize(rgb, (thumb_width, thumb_height), interpolation=cv2.INTER_AREA)
            pixmaps.append(self._rgb_to_pixmap(resized))

        return pixmaps

    @staticmethod
    def _rgb_to_pixmap(rgb: np.ndarray) -> QPixmap:
        h, w, _ = rgb.shape
        bytes_per_line = 3 * w
        image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
        return QPixmap.fromImage(image)

    def _show_frame(self, frame_index: int) -> None:
        try:
            rgb = self.reader.read_frame_rgb(frame_index)
        except Exception as exc:
            QMessageBox.warning(self, "Frame read error", str(exc))
            return

        self.preview.set_frame(rgb)
        self._update_comparison_view()

    def _build_comparison_rgb(self) -> np.ndarray | None:
        if self.reader.info is None:
            return None

        try:
            first_rgb = self._apply_crop(self.reader.read_frame_rgb(self.start_frame)).astype(np.float32)
            last_rgb = self._apply_crop(self.reader.read_frame_rgb(self.end_frame)).astype(np.float32)
        except Exception:
            return None

        tint_strength = 0.45
        overlay_alpha = 0.5

        blue_tint = np.array([80.0, 120.0, 255.0], dtype=np.float32)
        red_tint = np.array([255.0, 100.0, 100.0], dtype=np.float32)

        first_tinted = first_rgb * (1.0 - tint_strength) + blue_tint * tint_strength
        last_tinted = last_rgb * (1.0 - tint_strength) + red_tint * tint_strength

        blended = first_tinted * (1.0 - overlay_alpha) + last_tinted * overlay_alpha
        return np.clip(blended, 0, 255).astype(np.uint8)

    def _update_comparison_view(self) -> None:
        if not self.compare_toggle.isChecked() or self.reader.info is None:
            self.comparison_preview.hide()
            return

        comparison_rgb = self._build_comparison_rgb()
        if comparison_rgb is None:
            self.comparison_preview.setText("Comparison unavailable")
            self.comparison_preview.show()
            return

        pixmap = self._rgb_to_pixmap(comparison_rgb)
        scaled = pixmap.scaled(
            self.comparison_preview.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.comparison_preview.setPixmap(scaled)
        self.comparison_preview.show()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.reader.info is not None:
            self._show_frame(self.current_frame)
            self._update_comparison_view()

    def _get_crop_rect(self) -> tuple[int, int, int, int] | None:
        return self.preview.crop_rect()

    def _apply_crop(self, rgb: np.ndarray) -> np.ndarray:
        crop_rect = self._get_crop_rect()
        if crop_rect is None:
            return rgb

        x, y, width, height = crop_rect
        x = max(0, min(x, rgb.shape[1] - 1))
        y = max(0, min(y, rgb.shape[0] - 1))
        width = max(1, min(width, rgb.shape[1] - x))
        height = max(1, min(height, rgb.shape[0] - y))
        return rgb[y : y + height, x : x + width]

    @staticmethod
    def _format_size(num_bytes: int) -> str:
        size = float(max(0, num_bytes))
        units = ["B", "KB", "MB", "GB"]
        unit_index = 0
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        return f"{size:.1f} {units[unit_index]}"

    def _estimate_output_size_bytes(self) -> int | None:
        info = self.reader.info
        if info is None:
            return None

        target_fps = max(1, self.gif_fps_spin.value())
        step = max(1, int(round(info.fps / target_fps)))
        frame_count = len(range(self.start_frame, self.end_frame + 1, step))
        if frame_count <= 0:
            return None

        crop_rect = self._get_crop_rect()
        if crop_rect is None:
            src_w, src_h = info.width, info.height
        else:
            _, _, src_w, src_h = crop_rect

        out_w = max(1, self.gif_width_spin.value())
        out_h = max(1, int(src_h * (out_w / max(1, src_w))))
        duration_seconds = frame_count / target_fps
        quality = self.quality_spin.value() / 100.0
        output_format = self.format_combo.currentText().lower().strip()

        if output_format == "gif":
            raw_per_frame = out_w * out_h * 3
            compression_ratio = 3.0 + ((1.0 - quality) * 5.0)
            estimated = int(frame_count * (raw_per_frame / compression_ratio) + 24 * 1024)
            return max(1, estimated)

        bpp_map = {
            "webm": 0.07,
            "mp4": 0.09,
            "mpeg": 0.13,
        }
        base_bpp = bpp_map.get(output_format, 0.09)
        quality_scale = 0.6 + (quality * 0.8)
        bitrate = out_w * out_h * target_fps * base_bpp * quality_scale
        estimated = int((bitrate / 8.0) * duration_seconds + 64 * 1024)
        return max(1, estimated)

    def _update_size_estimate(self) -> None:
        estimated_bytes = self._estimate_output_size_bytes()
        if estimated_bytes is None:
            self.size_estimate_label.setText("Est size: —")
            return
        self.size_estimate_label.setText(f"Est size: {self._format_size(estimated_bytes)}")

    def on_timeline_current_changed(self, frame: int) -> None:
        self.current_frame = frame
        self._show_frame(frame)

    def on_timeline_range_changed(self, start: int, end: int) -> None:
        self.start_frame = start
        self.end_frame = end
        self._update_comparison_view()
        self._update_size_estimate()

    def on_compare_toggled(self, enabled: bool) -> None:
        if not enabled:
            self.comparison_preview.clear()
            self.comparison_preview.setText("Comparison disabled")
        self._update_comparison_view()

    def on_crop_changed(self, x: int, y: int, width: int, height: int) -> None:
        del x, y, width, height
        self._update_comparison_view()
        self._update_size_estimate()

    def on_export_settings_changed(self, value: int) -> None:
        del value
        self._update_size_estimate()

    def on_export_format_changed(self, value: str) -> None:
        del value
        self._update_size_estimate()

    def export_media(self) -> None:
        info = self.reader.info
        if info is None:
            return

        if self.end_frame <= self.start_frame:
            QMessageBox.warning(self, "Invalid range", "End must be greater than start.")
            return

        output_format = self.format_combo.currentText().lower().strip()
        format_defaults = {
            "gif": ("GIF files (*.gif)", ".gif"),
            "webm": ("WebM files (*.webm)", ".webm"),
            "mp4": ("MP4 files (*.mp4)", ".mp4"),
            "mpeg": ("MPEG files (*.mpeg *.mpg)", ".mpeg"),
        }
        selected_filter, default_suffix = format_defaults.get(output_format, format_defaults["gif"])

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Export",
            str(info.path.with_suffix(default_suffix)),
            selected_filter,
        )
        if not save_path:
            return

        save_path_lower = save_path.lower()
        if output_format == "mpeg":
            if not (save_path_lower.endswith(".mpeg") or save_path_lower.endswith(".mpg")):
                save_path = f"{save_path}.mpeg"
        elif not save_path_lower.endswith(f".{output_format}"):
            save_path = f"{save_path}.{output_format}"

        target_fps = self.gif_fps_spin.value()
        target_width = self.gif_width_spin.value()
        quality_percent = self.quality_spin.value()
        step = max(1, int(round(info.fps / target_fps)))

        frame_numbers = list(range(self.start_frame, self.end_frame + 1, step))
        total = len(frame_numbers)
        if total == 0:
            QMessageBox.warning(self, "No frames", "Selected range produced no frames.")
            return

        progress = QProgressDialog("Preparing frames...", "Cancel", 0, total, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)

        frames: list[np.ndarray] = []
        for index, frame_number in enumerate(frame_numbers, start=1):
            if progress.wasCanceled():
                return

            try:
                rgb = self.reader.read_frame_rgb(frame_number)
            except Exception as exc:
                QMessageBox.critical(self, "Export failed", str(exc))
                return

            rgb = self._apply_crop(rgb)

            src_h, src_w, _ = rgb.shape
            target_height = max(1, int(src_h * (target_width / src_w)))
            resized = cv2.resize(rgb, (target_width, target_height), interpolation=cv2.INTER_AREA)
            frames.append(resized)

            progress.setValue(index)
            progress.setLabelText(f"Preparing frames... {index}/{total}")
            QApplication.processEvents()

        try:
            if output_format == "gif":
                duration_ms = max(1, int(round(1000 / target_fps)))
                palette_colors = max(16, min(256, int(round(16 + (quality_percent / 100.0) * 240))))
                gif_frames = [
                    Image.fromarray(frame).convert("P", palette=Image.Palette.ADAPTIVE, colors=palette_colors)
                    for frame in frames
                ]
                first, rest = gif_frames[0], gif_frames[1:]
                first.save(
                    save_path,
                    save_all=True,
                    append_images=rest,
                    duration=duration_ms,
                    loop=0,
                    optimize=quality_percent >= 70,
                    disposal=2,
                )
            else:
                fourcc_map = {
                    "webm": "VP90",
                    "mp4": "mp4v",
                    "mpeg": "PIM1",
                }
                height, width, _ = frames[0].shape
                fourcc = cv2.VideoWriter_fourcc(*fourcc_map.get(output_format, "mp4v"))
                writer = cv2.VideoWriter(save_path, fourcc, float(target_fps), (width, height))
                if not writer.isOpened():
                    raise RuntimeError(f"Failed to initialize writer for format: {output_format}")

                try:
                    for frame in frames:
                        writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                finally:
                    writer.release()
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return

        progress.close()
        QMessageBox.information(self, "Done", f"Export saved:\n{save_path}")

from pathlib import Path

import cv2
import numpy as np

from .models import VideoInfo


class VideoReader:
    def __init__(self) -> None:
        self.capture: cv2.VideoCapture | None = None
        self.info: VideoInfo | None = None

    def open(self, file_path: str) -> VideoInfo:
        self.close()
        capture = cv2.VideoCapture(file_path)
        if not capture.isOpened():
            raise RuntimeError("Could not open video file.")

        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if frame_count <= 1:
            capture.release()
            raise RuntimeError("Video appears empty or unsupported.")
        if fps <= 0:
            fps = 24.0

        self.capture = capture
        self.info = VideoInfo(Path(file_path), frame_count, fps, width, height)
        return self.info

    def read_frame_rgb(self, frame_index: int) -> np.ndarray:
        if self.capture is None or self.info is None:
            raise RuntimeError("No video loaded.")

        idx = max(0, min(frame_index, self.info.frame_count - 1))
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame_bgr = self.capture.read()
        if not ok or frame_bgr is None:
            raise RuntimeError(f"Failed to read frame {idx}.")
        return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    def close(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        self.info = None

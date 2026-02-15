from dataclasses import dataclass
from pathlib import Path


@dataclass
class VideoInfo:
    path: Path
    frame_count: int
    fps: float
    width: int
    height: int

    @property
    def duration_seconds(self) -> float:
        return self.frame_count / self.fps if self.fps > 0 else 0.0

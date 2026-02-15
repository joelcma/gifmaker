import sys

from PySide6.QtWidgets import QApplication

from .main_window import GifMakerWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = GifMakerWindow()
    window.show()

    if len(sys.argv) > 1:
        window.load_video(sys.argv[1])

    return app.exec()

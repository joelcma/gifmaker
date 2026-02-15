try:
    from gifmaker_app.main import main
except ModuleNotFoundError as exc:
    if exc.name and exc.name.startswith("PySide6"):
        raise SystemExit(
            "PySide6 Qt modules are unavailable in this Python interpreter.\n"
            "Run with the project venv interpreter instead, for example:\n"
            "  /home/rob/tools/.venv/bin/python app.py <video-file>\n"
            "or activate the venv and run:\n"
            "  source /home/rob/tools/.venv/bin/activate && python app.py <video-file>"
        )
    raise


if __name__ == "__main__":
    raise SystemExit(main())


from pathlib import Path
import os
import sys
import ctypes

# PyInstaller's windowed bootloader leaves these streams as None. Libraries
# used while constructing the Tk UI may write warnings to them during startup.
# Keep those writes harmless instead of allowing an AttributeError to abort the
# GUI before the database and dashboard initialize.
if getattr(sys, "frozen", False):
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")

# Set a stable Windows taskbar identity before Tk creates the application
# window, so Windows associates the window with AuraPlan.exe's packaged icon.
if sys.platform == "win32":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AuraPlan.Desktop")
    except (AttributeError, OSError):
        pass

PROJECT_ROOT = Path(__file__).resolve().parent
for source_dir in ("app/backend", "app/ui"):
    path = str(PROJECT_ROOT / source_dir)
    if path not in sys.path:
        sys.path.insert(0, path)

from main_window import AuraPlanApp


def main():
    AuraPlanApp().run()


if __name__ == "__main__":
    main()

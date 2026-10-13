# AuraPlan icons

Place the application icon pack here:

- `auraplan.ico` — Windows window and taskbar icon. Use a multi-resolution ICO containing 16, 32, 48, and 256 px images.
- `auraplan.png` — Optional PNG fallback for the window icon.
- `theme-toggle.png` — Optional transparent 22 px (or larger square) icon for the light/dark control. The app shows a moon/sun glyph until this file is added.

When packaging with PyInstaller on Windows, embed the taskbar icon with `--icon "app/assets/icons/auraplan.ico"` and bundle these files with `--add-data "app/assets/icons;app/assets/icons"`.

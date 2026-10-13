"""Use CustomTkinter when installed; otherwise keep the demo runnable with Tk."""
import sys
from pathlib import Path

LIGHT_COLORS = {
    "forest": "#253D2C",
    "primary": "#2E6F40",
    "mint": "#CFFFDC",
    "leaf": "#68BA7F",
    "background": "#F3F8F4",
    "surface": "#FFFFFF",
    "surface_alt": "#EAF3EC",
    "text": "#253D2C",
    "muted": "#607766",
    "border": "#D6E5D9",
    "danger": "#A34242",
    "danger_surface": "#F8E8E6",
    "warning": "#8B621C",
}
DARK_COLORS = {
    **LIGHT_COLORS,
    "background": "#111914",
    "surface": "#1B2720",
    "surface_alt": "#24352A",
    "text": "#ECF5EE",
    "muted": "#B5C7B8",
    "border": "#3B5141",
    "danger": "#F19A91",
    "danger_surface": "#422D2C",
    "warning": "#EAC97E",
}
THEME_MODE = "light"
COLORS = dict(LIGHT_COLORS)
FONT_FAMILY = "Aptos"

try:
    import customtkinter as ctk
    import tkinter as tk
    from tkinter import messagebox
    CUSTOM = True
except ImportError:
    import tkinter as tk
    from tkinter import messagebox, ttk
    ctk = None
    CUSTOM = False


def root():
    if CUSTOM:
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        window = ctk.CTk()
        window.configure(fg_color=COLORS["background"])
        return window
    window = tk.Tk()
    style = ttk.Style(window)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(".", background=COLORS["background"], foreground=COLORS["text"],
                    font=(FONT_FAMILY, 11))
    style.configure("TFrame", background=COLORS["background"])
    style.configure("TLabel", background=COLORS["background"], foreground=COLORS["text"])
    style.configure("TButton", background=COLORS["primary"], foreground="white",
                    padding=(12, 8), borderwidth=0, focusthickness=0)
    style.map("TButton", background=[("active", COLORS["leaf"]), ("pressed", COLORS["forest"])])
    style.configure("TEntry", fieldbackground=COLORS["surface"], foreground=COLORS["text"],
                    bordercolor=COLORS["border"], padding=8)
    window.configure(bg=COLORS["background"])
    return window


def set_theme(mode, window=None):
    """Apply a light or dark palette; rebuild themed screens after calling."""
    global THEME_MODE
    THEME_MODE = "dark" if str(mode).casefold() == "dark" else "light"
    COLORS.clear()
    COLORS.update(DARK_COLORS if THEME_MODE == "dark" else LIGHT_COLORS)
    if CUSTOM:
        ctk.set_appearance_mode(THEME_MODE)
        if window is not None:
            window.configure(fg_color=COLORS["background"])
    elif window is not None:
        window.configure(bg=COLORS["background"])
        style = ttk.Style(window)
        style.configure(".", background=COLORS["background"], foreground=COLORS["text"],
                        font=(FONT_FAMILY, 11))
        style.configure("TFrame", background=COLORS["background"])
        style.configure("TLabel", background=COLORS["background"], foreground=COLORS["text"])
        style.configure("TButton", background=COLORS["primary"], foreground="white",
                        padding=(12, 8), borderwidth=0, focusthickness=0)
        style.map("TButton", background=[("active", COLORS["leaf"]),
                                          ("pressed", COLORS["forest"])])
        style.configure("TEntry", fieldbackground=COLORS["surface"], foreground=COLORS["text"],
                        bordercolor=COLORS["border"], padding=8)


def get_theme_mode():
    return THEME_MODE


def frame(master, **kw):
    if CUSTOM:
        kw.setdefault("corner_radius", 18)
        kw.setdefault("fg_color", COLORS["surface"])
        kw.setdefault("border_width", 0)
        return ctk.CTkFrame(master, **kw)
    for key in ("fg_color", "corner_radius", "border_width", "border_color"):
        kw.pop(key, None)
    return ttk.Frame(master, **kw)


def label(master, text="", **kw):
    if CUSTOM:
        kw.setdefault("font", (FONT_FAMILY, 11))
        kw.setdefault("text_color", COLORS["text"])
        return ctk.CTkLabel(master, text=text, **kw)
    kw.pop("text_color", None); kw.pop("fg_color", None)
    return ttk.Label(master, text=text, **kw)


def button(master, text, command=None, **kw):
    if CUSTOM:
        kw.setdefault("font", (FONT_FAMILY, 12, "bold"))
        kw.setdefault("corner_radius", 13)
        kw.setdefault("fg_color", COLORS["primary"])
        kw.setdefault("hover_color", COLORS["forest"])
        kw.setdefault("text_color", "#FFFFFF")
        return ctk.CTkButton(master, text=text, command=command, **kw)
    for key in ("fg_color", "hover_color", "text_color", "corner_radius", "border_width", "border_color", "height", "anchor"):
        kw.pop(key, None)
    return ttk.Button(master, text=text, command=command, **kw)


def entry(master, variable=None, placeholder=None, **kw):
    if CUSTOM:
        kw.setdefault("font", (FONT_FAMILY, 12))
        kw.setdefault("corner_radius", 12)
        kw.setdefault("border_color", COLORS["border"])
        kw.setdefault("border_width", 1)
        kw.setdefault("height", 38)
        kw.setdefault("text_color", COLORS["text"])
        kw.setdefault("fg_color", COLORS["surface"])
        kw.setdefault("placeholder_text_color", COLORS["muted"])
        return ctk.CTkEntry(master, textvariable=variable, placeholder_text=placeholder, **kw)
    kw.pop("placeholder_text", None); kw.pop("border_color", None); kw.pop("height", None)
    return ttk.Entry(master, textvariable=variable, **kw)


def textbox(master, **kw):
    if CUSTOM:
        kw.setdefault("font", (FONT_FAMILY, 12))
        kw.setdefault("corner_radius", 12)
        kw.setdefault("border_color", COLORS["border"])
        kw.setdefault("fg_color", COLORS["surface"])
        kw.setdefault("text_color", COLORS["text"])
        return ctk.CTkTextbox(master, **kw)
    for key in ("border_color", "corner_radius", "fg_color", "text_color"):
        kw.pop(key, None)
    kw.setdefault("background", COLORS["surface"])
    kw.setdefault("foreground", COLORS["text"])
    kw.setdefault("insertbackground", COLORS["text"])
    kw.setdefault("relief", "flat")
    return tk.Text(master, **kw)


def option_menu(master, values, variable, command=None, **kw):
    if CUSTOM:
        kw.setdefault("fg_color", COLORS["primary"])
        kw.setdefault("button_color", COLORS["primary"])
        kw.setdefault("button_hover_color", COLORS["forest"])
        kw.setdefault("text_color", "#FFFFFF")
        kw.setdefault("dropdown_fg_color", COLORS["surface"])
        kw.setdefault("dropdown_hover_color", COLORS["surface_alt"])
        kw.setdefault("dropdown_text_color", COLORS["text"])
        return ctk.CTkOptionMenu(master, values=values, variable=variable, command=command, **kw)
    for key in ("height", "fg_color", "button_color", "button_hover_color", "text_color",
                "dropdown_fg_color", "dropdown_hover_color", "dropdown_text_color"):
        kw.pop(key, None)
    return ttk.Combobox(master, values=values, textvariable=variable, state="readonly", **kw)


def energy_selector(master, values, variable):
    """Show all energy stages at once instead of hiding them in a menu."""
    if CUSTOM:
        dark_mode = THEME_MODE == "dark"
        return ctk.CTkSegmentedButton(
            master, values=values, variable=variable, corner_radius=12,
            selected_color=COLORS["primary"],
            selected_hover_color=COLORS["primary"] if dark_mode else COLORS["leaf"],
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["surface"] if dark_mode else COLORS["mint"],
            text_color=COLORS["mint"] if THEME_MODE == "dark" else COLORS["forest"],
        )
    selector = ttk.Frame(master)
    for value in values:
        ttk.Radiobutton(selector, text=value, value=value, variable=variable).pack(side="left", padx=3)
    return selector


def brand_mark_image(master, size=40):
    """Load AuraPlan's emblem cropped from the supplied logo artwork."""
    try:
        from PIL import Image, ImageTk

        bundled_root = getattr(sys, "_MEIPASS", None)
        icons_dir = (Path(bundled_root) / "app" / "assets" / "icons" if bundled_root
                     else Path(__file__).resolve().parents[1] / "assets" / "icons")
        with Image.open(icons_dir / "auraplan.png") as source:
            source = source.convert("RGBA")
            width, height = source.size
            if abs(width - height) / max(width, height) < 0.12:
                # Recent AuraPlan artwork is already a square emblem; cropping
                # it like the former tall wordmark would cut off the logo.
                mark = source
            else:
                # Older artwork had a wordmark below the circular A emblem.
                mark = source.crop((int(width * .22), int(height * .14),
                                    int(width * .78), int(height * .68)))
                side = min(mark.size)
                left = (mark.width - side) // 2
                top = (mark.height - side) // 2
                mark = mark.crop((left, top, left + side, top + side))
            resampling = getattr(Image, "Resampling", Image).LANCZOS
            mark = mark.resize((size * 2, size * 2), resampling)
        if CUSTOM:
            return ctk.CTkImage(light_image=mark, dark_image=mark, size=(size, size))
        return ImageTk.PhotoImage(mark, master=master)
    except Exception:
        return None


def progress(master, **kw):
    if CUSTOM:
        kw.setdefault("progress_color", COLORS["leaf"])
        kw.setdefault("fg_color", COLORS["mint"])
        kw.setdefault("corner_radius", 8)
        return ctk.CTkProgressBar(master, **kw)
    if "width" in kw:
        kw["length"] = kw.pop("width")
    for key in ("height", "fg_color", "progress_color", "corner_radius"):
        kw.pop(key, None)
    return ttk.Progressbar(master, mode="determinate", maximum=100, **kw)


def set_progress(widget, value):
    """Set a normalized 0-100 progress value in either UI toolkit."""
    value = max(0.0, min(100.0, float(value)))
    if CUSTOM:
        widget.set(value / 100.0)
    else:
        widget.configure(value=value)


def scrollable(master, **kw):
    if CUSTOM:
        kw.setdefault("fg_color", "transparent")
        kw.setdefault("corner_radius", 16)
        kw.setdefault("border_width", 0)
        return ctk.CTkScrollableFrame(master, **kw)
    container = ttk.Frame(master)
    canvas = tk.Canvas(container, highlightthickness=0, height=350)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    inner = ttk.Frame(canvas)
    inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
    container.inner = inner
    return container

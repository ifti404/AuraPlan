
import sys
from pathlib import Path

import customtkinter as ctk
from PIL import Image

# Backend path
BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from task_repository import TaskRepository

from app.ui.themes.palette import DARK_COLORS, LIGHT_COLORS
from app.ui.pages.dashboard import DashboardPage
from app.ui.pages.tasks import TasksPage
from app.ui.pages.schedule import SchedulePage
from app.ui.pages.focus import FocusPage
from app.ui.pages.voice import VoicePage
from app.ui.pages.settings import SettingsPage


class AuraPlanApp(ctk.CTk):

    NAV_ITEMS = [
        ("Dashboard", "▦", "Dashboard"),
        ("Tasks", "☷", "My Tasks"),
        ("Schedule", "▤", "Smart Schedule"),
        ("Focus", "◷", "Focus Mode"),
        ("Voice", "♫", "Voice Assistant"),
        ("Settings", "⚙", "Settings"),
    ]

    def __init__(self):
        super().__init__()

        self.title("AuraPlan | Study & Productivity Planner")
        self.geometry("1280x800")
        self.minsize(1050, 680)

        self.is_dark = False
        self.colors = LIGHT_COLORS
        self.current_page = "Dashboard"

        self.repository = TaskRepository()

        ctk.set_appearance_mode("Light")
        self.configure(fg_color=self.colors["background"])

        self.create_layout()
        self.show_page("Dashboard")

    # -------------------------------
    # MAIN WINDOW LAYOUT
    # -------------------------------

    def create_layout(self):

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_header()
        self.create_sidebar()
        self.create_main_area()

    # -------------------------------
    # HEADER
    # -------------------------------

    def create_header(self):

        self.header = ctk.CTkFrame(
            self,
            height=78,
            corner_radius=0,
            fg_color=self.colors["header"]
        )

        self.header.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew"
        )

        self.header.grid_propagate(False)
        self.header.grid_columnconfigure(1, weight=1)

        # Logo and brand section
        brand = ctk.CTkFrame(
            self.header,
            fg_color="transparent"
        )

        brand.grid(
            row=0,
            column=0,
            sticky="w",
            padx=22,
            pady=10
        )

        project_root = Path(__file__).resolve().parents[2]
        logo_candidates = [
            project_root / "assets" / "auraplan_logo.png",
            project_root / "assets" / "icons" / "auraplan.png",
            project_root.parent / "assets" / "auraplan_logo.png",
        ]
        logo_path = next((path for path in logo_candidates if path.exists()), None)
        self.logo_image = None
        if logo_path is not None:
            try:
                logo = Image.open(logo_path).convert("RGBA")
                self.logo_image = ctk.CTkImage(
                    light_image=logo, dark_image=logo, size=(52, 52)
                )
                ctk.CTkLabel(brand, text="", image=self.logo_image).pack(
                    side="left", padx=(0, 10)
                )
            except Exception:
                self.logo_image = None

        if self.logo_image is None:
            ctk.CTkLabel(
                brand, text="A", width=46, height=46, corner_radius=12,
                fg_color=self.colors["accent"], text_color="#214C3A",
                font=("Segoe UI", 25, "bold")
            ).pack(side="left", padx=(0, 10))

        brand_text = ctk.CTkFrame(
            brand,
            fg_color="transparent"
        )

        brand_text.pack(side="left")

        ctk.CTkLabel(
            brand_text,
            text="AuraPlan",
            font=("Segoe UI", 22, "bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_text,
            text="STUDY  •  PLAN  •  GROW",
            font=("Segoe UI", 9, "bold"),
            text_color="#D5E8DC"
        ).pack(anchor="w")

        # Search bar
        self.search_entry = ctk.CTkEntry(
            self.header,
            width=270,
            height=38,
            corner_radius=20,
            placeholder_text="Search your tasks...",
            fg_color=self.colors["surface"],
            text_color=self.colors["text"],
            placeholder_text_color=self.colors["muted"],
            border_width=1,
            border_color=self.colors["border"]
        )

        self.search_entry.grid(
            row=0,
            column=1,
            sticky="w",
            padx=28,
            pady=20
        )

        # Header right section
        right = ctk.CTkFrame(
            self.header,
            fg_color="transparent"
        )

        right.grid(
            row=0,
            column=2,
            sticky="e",
            padx=22
        )

        self.theme_button = ctk.CTkButton(
            right,
            text="☼  /  ☾",
            width=82,
            height=36,
            corner_radius=18,
            fg_color=self.colors["surface"],
            text_color=self.colors["text"],
            hover_color=self.colors["highlight"],
            command=self.toggle_theme
        )

        self.theme_button.pack(side="left", padx=8)

        profile = ctk.CTkFrame(
            right,
            fg_color=self.colors["surface"],
            corner_radius=20
        )

        profile.pack(side="left", padx=5)

        ctk.CTkLabel(
            profile,
            text="  My Study Space  ",
            font=("Segoe UI", 12, "bold"),
            text_color=self.colors["text"]
        ).pack(padx=8, pady=9)

    # -------------------------------
    # SIDEBAR
    # -------------------------------

    def create_sidebar(self):

        self.sidebar = ctk.CTkFrame(
            self,
            width=205,
            corner_radius=0,
            fg_color=self.colors["sidebar"]
        )

        self.sidebar.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        self.sidebar.grid_propagate(False)

        self.nav_buttons = {}

        ctk.CTkLabel(
            self.sidebar,
            text="WORKSPACE",
            font=("Segoe UI", 10, "bold"),
            text_color=self.colors["muted"]
        ).pack(
            anchor="w",
            padx=23,
            pady=(27, 12)
        )

        for name, symbol, label in self.NAV_ITEMS:

            button = ctk.CTkButton(
                self.sidebar,
                text=f"  {symbol}     {label}",
                height=45,
                corner_radius=12,
                anchor="w",
                font=("Segoe UI", 13, "bold"),
                fg_color="transparent",
                hover_color=self.colors["highlight"],
                text_color=self.colors["text"],
                command=lambda page=name: self.show_page(page)
            )

            button.pack(
                fill="x",
                padx=13,
                pady=4
            )

            self.nav_buttons[name] = button

        # Study reminder card
        reminder = ctk.CTkFrame(
            self.sidebar,
            fg_color=self.colors["surface_alt"],
            corner_radius=14
        )

        reminder.pack(
            side="bottom",
            fill="x",
            padx=13,
            pady=18
        )

        ctk.CTkLabel(
            reminder,
            text="✦  DAILY REMINDER",
            font=("Segoe UI", 10, "bold"),
            text_color=self.colors["primary"]
        ).pack(
            anchor="w",
            padx=12,
            pady=(12, 5)
        )

        ctk.CTkLabel(
            reminder,
            text="Small steps every day\nlead to big results.",
            font=("Segoe UI", 12),
            justify="left",
            text_color=self.colors["text"]
        ).pack(
            anchor="w",
            padx=12,
            pady=(0, 12)
        )

    # -------------------------------
    # MAIN CONTENT AREA
    # -------------------------------

    def create_main_area(self):

        self.main_area = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=self.colors["background"]
        )

        self.main_area.grid(
            row=1,
            column=1,
            sticky="nsew",
            padx=22,
            pady=20
        )

        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)

    # -------------------------------
    # PAGE NAVIGATION
    # -------------------------------

    def show_page(self, name):

        self.current_page = name

        for widget in self.main_area.winfo_children():
            widget.destroy()

        if name == "Dashboard":

            page = DashboardPage(
                self.main_area,
                self.colors,
                self.repository
            )

        elif name == "Tasks":

            page = TasksPage(
                self.main_area,
                self.colors,
                self.repository
            )

        elif name == "Schedule":

            page = SchedulePage(
                self.main_area,
                self.colors,
                self.repository
            )

        elif name == "Focus":

            page = FocusPage(
                self.main_area,
                self.colors
            )

        elif name == "Voice":

            page = VoicePage(
                self.main_area,
                self.colors
            )

        elif name == "Settings":

            page = SettingsPage(
                self.main_area,
                self.colors,
                self.toggle_theme
            )

        else:
            return

        page.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        # Active navigation styling
        for button_name, button in self.nav_buttons.items():

            active = button_name == name

            button.configure(
                fg_color=(
                    self.colors["accent"]
                    if active
                    else "transparent"
                ),
                text_color=("#214C3A" if active else self.colors["text"]),
                hover_color=self.colors["highlight"]
            )

    # -------------------------------
    # THEME SWITCH
    # -------------------------------

    def toggle_theme(self):

        self.is_dark = not self.is_dark
        self.colors = DARK_COLORS if self.is_dark else LIGHT_COLORS
        ctk.set_appearance_mode("Dark" if self.is_dark else "Light")

        self.configure(fg_color=self.colors["background"])
        self.header.configure(fg_color=self.colors["header"])
        self.sidebar.configure(fg_color=self.colors["sidebar"])
        self.main_area.configure(fg_color=self.colors["background"])

        # Rebuild sidebar so every label and navigation item uses the new palette.
        self.sidebar.destroy()
        self.create_sidebar()

        # Refresh header controls so their colors match the selected theme.
        self.search_entry.configure(
            fg_color=self.colors["surface"],
            text_color=self.colors["text"],
            placeholder_text_color=self.colors["muted"],
            border_color=self.colors["border"],
        )
        self.theme_button.configure(
            fg_color=self.colors["surface"],
            text_color=self.colors["text"],
            hover_color=self.colors["highlight"],
        )
        for child in self.header.winfo_children():
            if child is not self.search_entry and child is not self.theme_button:
                self._recolor_header_tree(child)

        self.show_page(self.current_page)

    def _recolor_header_tree(self, widget):
        """Apply current palette to header labels and frames after theme change."""
        try:
            if isinstance(widget, ctk.CTkFrame):
                current = widget.cget("fg_color")
                if current not in ("transparent", "#FFFFFF", "white"):
                    widget.configure(fg_color=self.colors["surface"])
            elif isinstance(widget, ctk.CTkLabel):
                text = widget.cget("text")
                if text == "AuraPlan":
                    widget.configure(text_color="#FFFFFF")
                elif text == "STUDY  •  PLAN  •  GROW":
                    widget.configure(text_color="#D5E8DC")
                else:
                    widget.configure(text_color=self.colors["text"])
        except Exception:
            pass
        try:
            for child in widget.winfo_children():
                self._recolor_header_tree(child)
        except Exception:
            pass

    # -------------------------------
    # APPLICATION START
    # -------------------------------

    def run(self):
        self.mainloop()


if __name__ == "__main__":
    app = AuraPlanApp()
    app.run()

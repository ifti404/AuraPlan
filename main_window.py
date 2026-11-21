
import customtkinter as ctk
from theme import COLORS, FONT, setup_theme


class AuraPlanApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        setup_theme()

        self.title("AuraPlan - Smart Productivity")
        self.geometry("1280x800")
        self.minsize(1100, 700)

        self.configure(fg_color=COLORS["background"])

        # Main Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_area()

    def create_sidebar(self):

        self.sidebar = ctk.CTkFrame(
            self,
            width=240,
            corner_radius=0,
            fg_color=COLORS["sidebar"]
        )

        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Logo
        logo = ctk.CTkLabel(
            self.sidebar,
            text="✦ AuraPlan",
            font=(FONT, 25, "bold"),
            text_color=COLORS["primary"]
        )
        logo.pack(pady=(35, 45))

        # Navigation
        menu_items = [
            "Dashboard",
            "My Tasks",
            "Add Task",
            "Smart Schedule",
            "Voice Assistant",
            "Focus Room",
            "Settings"
        ]

        self.nav_buttons = {}

        for item in menu_items:

            button = ctk.CTkButton(
                self.sidebar,
                text=f"   {item}",
                height=45,
                corner_radius=10,
                anchor="w",
                fg_color="transparent",
                hover_color=COLORS["primary_light"],
                text_color=COLORS["text"],
                font=(FONT, 14),
                command=lambda name=item: self.show_page(name)
            )

            button.pack(fill="x", padx=18, pady=5)
            self.nav_buttons[item] = button

    def create_main_area(self):

        self.main_area = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=COLORS["background"]
        )

        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(1, weight=1)

        self.header = ctk.CTkLabel(
            self.main_area,
            text="Dashboard",
            font=(FONT, 28, "bold"),
            text_color=COLORS["navy"]
        )

        self.header.grid(
            row=0, column=0,
            sticky="w",
            padx=35, pady=30
        )

        self.page_container = ctk.CTkFrame(
            self.main_area,
            fg_color="transparent"
        )

        self.page_container.grid(
            row=1, column=0,
            sticky="nsew",
            padx=35, pady=(0, 30)
        )

        self.show_page("Dashboard")

    def show_page(self, page_name):

        self.header.configure(text=page_name)

        for widget in self.page_container.winfo_children():
            widget.destroy()

        if page_name == "Dashboard":
            ctk.CTkLabel(
                self.page_container,
                text="Welcome to AuraPlan!",
                font=(FONT, 26, "bold"),
                text_color=COLORS["navy"]
            ).pack(anchor="w", pady=20)

            ctk.CTkLabel(
                self.page_container,
                text="Your productivity journey starts here.",
                font=(FONT, 15),
                text_color=COLORS["muted"]
            ).pack(anchor="w")

        else:
            ctk.CTkLabel(
                self.page_container,
                text=f"{page_name} Page",
                font=(FONT, 24, "bold"),
                text_color=COLORS["navy"]
            ).pack(anchor="w", pady=20)

        for name, button in self.nav_buttons.items():
            if name == page_name:
                button.configure(
                    fg_color=COLORS["primary_light"],
                    text_color=COLORS["primary"]
                )
            else:
                button.configure(
                    fg_color="transparent",
                    text_color=COLORS["text"]
                )

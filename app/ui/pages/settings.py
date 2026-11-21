import customtkinter as ctk


class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, colors, theme_callback):
        super().__init__(parent, fg_color="transparent")
        self.colors = colors
        self.theme_callback = theme_callback
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(
            self, text="Settings", font=("Segoe UI", 28, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", pady=(10, 5))
        ctk.CTkLabel(
            self, text="Customize your AuraPlan experience.",
            font=("Segoe UI", 14), text_color=self.colors["muted"]
        ).pack(anchor="w", pady=(0, 22))

        appearance = ctk.CTkFrame(
            self, fg_color=self.colors["surface"], corner_radius=18,
            border_width=1, border_color=self.colors["border"]
        )
        appearance.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(
            appearance, text="Appearance", font=("Segoe UI", 19, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", padx=22, pady=(20, 6))
        ctk.CTkLabel(
            appearance, text="Switch between the Light and Dark workspace themes.",
            font=("Segoe UI", 13), text_color=self.colors["muted"]
        ).pack(anchor="w", padx=22, pady=(0, 12))
        ctk.CTkButton(
            appearance, text="Switch Dark / Light Theme", width=225, height=40,
            command=self.theme_callback
        ).pack(anchor="w", padx=22, pady=(0, 22))

        info = ctk.CTkFrame(
            self, fg_color=self.colors["surface"], corner_radius=18,
            border_width=1, border_color=self.colors["border"]
        )
        info.pack(fill="x", pady=14)
        ctk.CTkLabel(
            info, text="About AuraPlan", font=("Segoe UI", 19, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", padx=22, pady=(20, 8))
        ctk.CTkLabel(
            info,
            text="AuraPlan — Your Study & Productivity Planner\nVersion 1.0",
            font=("Segoe UI", 13), text_color=self.colors["muted"],
            justify="left"
        ).pack(anchor="w", padx=22, pady=(0, 20))

        privacy = ctk.CTkFrame(
            self, fg_color=self.colors["surface_alt"], corner_radius=14
        )
        privacy.pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(
            privacy, text="LOCAL WORKSPACE", font=("Segoe UI", 11, "bold"),
            text_color=self.colors["primary"]
        ).pack(anchor="w", padx=18, pady=(14, 4))
        ctk.CTkLabel(
            privacy,
            text="Your tasks are stored in the local AuraPlan database on this device.",
            font=("Segoe UI", 12), text_color=self.colors["text"],
            wraplength=700, justify="left"
        ).pack(anchor="w", padx=18, pady=(0, 14))

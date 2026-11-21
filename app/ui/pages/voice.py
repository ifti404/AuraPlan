
import customtkinter as ctk


class VoicePage(ctk.CTkFrame):

    def __init__(self, parent, colors):
        super().__init__(parent, fg_color="transparent")
        self.colors = colors
        self.create_widgets()

    def create_widgets(self):

        ctk.CTkLabel(
            self,
            text="Voice Assistant",
            font=("Segoe UI", 28, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", pady=(10, 5))

        ctk.CTkLabel(
            self,
            text="Add tasks using your voice.",
            font=("Segoe UI", 14),
            text_color=self.colors["muted"]
        ).pack(anchor="w", pady=(0, 25))

        card = ctk.CTkFrame(
            self,
            fg_color=self.colors["surface"],
            corner_radius=16
        )
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            card,
            text="Voice Input",
            font=("Segoe UI", 20, "bold"),
            text_color=self.colors["text"]
        ).pack(pady=(35, 15))

        self.mic_button = ctk.CTkButton(
            card,
            text="🎙  Start Listening",
            width=190,
            height=55,
            font=("Segoe UI", 16, "bold"),
            command=self.show_status
        )
        self.mic_button.pack(pady=15)

        self.status_label = ctk.CTkLabel(
            card,
            text="Voice recognition is not connected yet.",
            font=("Segoe UI", 12),
            text_color=self.colors["muted"]
        )
        self.status_label.pack(pady=10)

        ctk.CTkLabel(
            card,
            text="Recognized Text",
            font=("Segoe UI", 16, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", padx=35, pady=(25, 10))

        self.text_input = ctk.CTkTextbox(
            card,
            height=130,
            corner_radius=10,
            fg_color=self.colors["surface_alt"],
            text_color=self.colors["text"]
        )
        self.text_input.pack(fill="x", padx=35)

        ctk.CTkLabel(
            card,
            text="Review the recognized text before using it.",
            font=("Segoe UI", 11),
            text_color=self.colors["muted"]
        ).pack(anchor="w", padx=35, pady=10)

    def show_status(self):
        self.status_label.configure(
            text="Microphone backend needs to be connected."
        )

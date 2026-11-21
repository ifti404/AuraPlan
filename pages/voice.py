
import threading
from pathlib import Path

import customtkinter as ctk
from tkinter import messagebox


class VoicePage(ctk.CTkFrame):

    def __init__(self, parent, colors):
        super().__init__(parent, fg_color="transparent")

        self.colors = colors
        self.voice_input = None
        self.voice_session = None
        self.loading = False
        self.listening = False

        self.model_path = Path(__file__).resolve().parents[3] / "model"

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
            text="Capture your ideas using offline voice recognition.",
            font=("Segoe UI", 14),
            text_color=self.colors["muted"]
        ).pack(anchor="w", pady=(0, 20))

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
        ).pack(pady=(30, 12))

        self.mic_button = ctk.CTkButton(
            card,
            text="Start Listening",
            width=200,
            height=48,
            font=("Segoe UI", 15, "bold"),
            command=self.toggle_listening
        )
        self.mic_button.pack(pady=10)

        self.status_label = ctk.CTkLabel(
            card,
            text="Ready. Press Start Listening to begin.",
            text_color=self.colors["muted"]
        )
        self.status_label.pack(pady=8)

        ctk.CTkLabel(
            card,
            text="Recognized Text",
            font=("Segoe UI", 16, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", padx=30, pady=(22, 8))

        self.text_input = ctk.CTkTextbox(
            card,
            height=170,
            corner_radius=10,
            fg_color=self.colors["surface_alt"],
            text_color=self.colors["text"]
        )
        self.text_input.pack(fill="x", padx=30)

        ctk.CTkLabel(
            card,
            text="Review and edit the recognized text before using it.",
            font=("Segoe UI", 11),
            text_color=self.colors["muted"]
        ).pack(anchor="w", padx=30, pady=10)

        ctk.CTkButton(
            card,
            text="Clear Text",
            width=100,
            height=32,
            fg_color=self.colors["surface_alt"],
            text_color=self.colors["text"],
            command=self.clear_text
        ).pack(anchor="e", padx=30, pady=(0, 25))

    def toggle_listening(self):
        if self.listening:
            self.stop_listening()
            return

        if self.loading:
            return

        if self.voice_input is not None:
            self.start_session()
            return

        self.load_voice_model()

    def load_voice_model(self):
        if not self.model_path.is_dir():
            messagebox.showerror(
                "Vosk model not found",
                "The offline model folder was not found.\n\n"
                f"Expected location:\n{self.model_path}",
                parent=self
            )
            return

        self.loading = True
        self.mic_button.configure(
            text="Loading model...",
            state="disabled"
        )
        self.status_label.configure(
            text="Loading offline voice model. Please wait..."
        )

        threading.Thread(
            target=self._load_model_worker,
            daemon=True
        ).start()

    def _load_model_worker(self):
        try:
            from app.voices.voice_input import VoiceInput
            voice_input = VoiceInput(model_path=self.model_path)
            self.after(
                0, lambda: self._model_loaded(voice_input, None)
            )
        except Exception as exc:
            self.after(
                0, lambda error=str(exc): self._model_loaded(None, error)
            )

    def _model_loaded(self, voice_input, error):
        self.loading = False

        if error:
            self.mic_button.configure(
                text="Start Listening",
                state="normal"
            )
            self.status_label.configure(
                text="Could not load voice model."
            )
            messagebox.showerror(
                "Voice setup error", error, parent=self
            )
            return

        self.voice_input = voice_input
        self.start_session()

    def start_session(self):
        try:
            from app.voices.voice_session import VoiceSession

            self.voice_session = VoiceSession(
                self.voice_input,
                self._session_started,
                self._session_finished
            )
            self.voice_session.start()

            self.mic_button.configure(
                text="Stop Listening",
                state="normal",
                fg_color=self.colors["danger"]
            )
            self.status_label.configure(
                text="Opening microphone..."
            )

        except Exception as exc:
            self.listening = False
            self.mic_button.configure(
                text="Start Listening",
                state="normal"
            )
            messagebox.showerror(
                "Voice error", str(exc), parent=self
            )

    def _session_started(self):
        self.after(0, self._show_listening)

    def _show_listening(self):
        self.listening = True
        self.status_label.configure(
            text="Listening... Speak now. Press Stop when finished."
        )

    def stop_listening(self):
        if self.voice_session is not None:
            self.voice_session.stop()

        self.status_label.configure(
            text="Stopping microphone..."
        )
        self.mic_button.configure(state="disabled")

    def _session_finished(self, transcript, error):
        self.after(
            0,
            lambda text=transcript, err=error:
                self._show_result(text, err)
        )

    def _show_result(self, transcript, error):
        self.listening = False
        self.voice_session = None

        self.mic_button.configure(
            text="Start Listening",
            state="normal",
            fg_color=self.colors["primary"]
        )

        if error:
            self.status_label.configure(
                text="Voice recognition stopped with an error."
            )
            messagebox.showerror(
                "Microphone error", error, parent=self
            )
            return

        if transcript:
            current = self.text_input.get("1.0", "end").strip()
            self.text_input.delete("1.0", "end")

            combined = f"{current} {transcript}".strip()
            self.text_input.insert("1.0", combined)

            self.status_label.configure(
                text="Speech recognized. Review the text above."
            )
        else:
            self.status_label.configure(
                text="No speech recognized. Try again."
            )

    def clear_text(self):
        self.text_input.delete("1.0", "end")

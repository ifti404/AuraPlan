import customtkinter as ctk


class FocusPage(ctk.CTkFrame):
    """A lightweight Pomodoro-style focus timer."""

    PRESETS = (15, 25, 45, 60)

    def __init__(self, parent, colors):
        super().__init__(parent, fg_color="transparent")
        self.colors = colors
        self.duration_minutes = 25
        self.remaining_seconds = self.duration_minutes * 60
        self.timer_running = False
        self.timer_job = None
        self.completed_sessions = 0
        self.create_widgets()
        self._render_time()

    def create_widgets(self):
        ctk.CTkLabel(
            self, text="Focus Mode", font=("Segoe UI", 28, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", pady=(10, 5))
        ctk.CTkLabel(
            self, text="Work in focused sessions and take control of your study time.",
            font=("Segoe UI", 14), text_color=self.colors["muted"]
        ).pack(anchor="w", pady=(0, 22))

        card = ctk.CTkFrame(
            self, fg_color=self.colors["surface"], corner_radius=20,
            border_width=1, border_color=self.colors["border"]
        )
        card.pack(fill="both", expand=True, pady=(0, 8))

        ctk.CTkLabel(
            card, text="FOCUS SESSION", font=("Segoe UI", 13, "bold"),
            text_color=self.colors["muted"]
        ).pack(pady=(32, 10))

        self.timer_label = ctk.CTkLabel(
            card, text="25:00", font=("Segoe UI", 68, "bold"),
            text_color=self.colors["primary"]
        )
        self.timer_label.pack(pady=(4, 6))

        self.status_label = ctk.CTkLabel(
            card, text="Ready when you are.", font=("Segoe UI", 13),
            text_color=self.colors["muted"]
        )
        self.status_label.pack(pady=(0, 18))

        preset_frame = ctk.CTkFrame(card, fg_color="transparent")
        preset_frame.pack(pady=4)
        ctk.CTkLabel(
            preset_frame, text="Session length", font=("Segoe UI", 12, "bold"),
            text_color=self.colors["text"]
        ).pack(side="left", padx=(0, 12))
        self.duration_menu = ctk.CTkOptionMenu(
            preset_frame, values=[str(x) for x in self.PRESETS],
            width=92, height=34, command=self.set_duration,
            fg_color=self.colors["primary"], button_color=self.colors["primary"],
            button_hover_color=self.colors["highlight"], text_color="#FFFFFF"
        )
        self.duration_menu.set("25")
        self.duration_menu.pack(side="left")
        ctk.CTkLabel(
            preset_frame, text="minutes", font=("Segoe UI", 12),
            text_color=self.colors["muted"]
        ).pack(side="left", padx=(8, 0))

        self.progress = ctk.CTkProgressBar(
            card, width=360, height=9, progress_color=self.colors["primary"],
            fg_color=self.colors["surface_alt"]
        )
        self.progress.pack(pady=(22, 20))
        self.progress.set(0)

        controls = ctk.CTkFrame(card, fg_color="transparent")
        controls.pack(pady=(0, 18))
        self.start_button = ctk.CTkButton(
            controls, text="Start", width=112, height=42,
            font=("Segoe UI", 13, "bold"), command=self.start_timer
        )
        self.start_button.pack(side="left", padx=7)
        self.pause_button = ctk.CTkButton(
            controls, text="Pause", width=112, height=42,
            fg_color=self.colors["surface_alt"], text_color=self.colors["text"],
            hover_color=self.colors["highlight"], command=self.pause_timer
        )
        self.pause_button.pack(side="left", padx=7)
        ctk.CTkButton(
            controls, text="Reset", width=112, height=42,
            fg_color=self.colors["surface_alt"], text_color=self.colors["text"],
            hover_color=self.colors["highlight"], command=self.reset_timer
        ).pack(side="left", padx=7)

        self.sessions_label = ctk.CTkLabel(
            card, text="Completed sessions: 0", font=("Segoe UI", 12, "bold"),
            text_color=self.colors["muted"]
        )
        self.sessions_label.pack(pady=(4, 24))

    def set_duration(self, value):
        if self.timer_running:
            return
        try:
            minutes = int(value)
        except (TypeError, ValueError):
            return
        if minutes not in self.PRESETS:
            return
        self.duration_minutes = minutes
        self.remaining_seconds = minutes * 60
        self.status_label.configure(text="Session length updated.")
        self._render_time()

    def start_timer(self):
        if self.timer_running:
            return
        if self.remaining_seconds <= 0:
            self.remaining_seconds = self.duration_minutes * 60
        self.timer_running = True
        self.status_label.configure(text="Focus session in progress…")
        self._tick()

    def _tick(self):
        if not self.timer_running:
            return
        if self.remaining_seconds <= 0:
            self.timer_running = False
            self.timer_job = None
            self.completed_sessions += 1
            self.sessions_label.configure(
                text=f"Completed sessions: {self.completed_sessions}"
            )
            self.status_label.configure(text="Session complete. Great work!")
            self.progress.set(1)
            self.timer_label.configure(text="00:00")
            return
        self._render_time()
        self.remaining_seconds -= 1
        self.timer_job = self.after(1000, self._tick)

    def _render_time(self):
        minutes, seconds = divmod(max(0, self.remaining_seconds), 60)
        self.timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")
        total = max(1, self.duration_minutes * 60)
        self.progress.set(1 - (self.remaining_seconds / total))

    def pause_timer(self):
        if self.timer_running:
            self.timer_running = False
            if self.timer_job is not None:
                try:
                    self.after_cancel(self.timer_job)
                except Exception:
                    pass
                self.timer_job = None
            self.status_label.configure(text="Session paused.")

    def reset_timer(self):
        self.pause_timer()
        self.remaining_seconds = self.duration_minutes * 60
        self.status_label.configure(text="Timer reset. Ready when you are.")
        self._render_time()

    def destroy(self):
        self.pause_timer()
        super().destroy()

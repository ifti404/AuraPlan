from datetime import datetime

import customtkinter as ctk


class DashboardPage(ctk.CTkFrame):
    """Live overview of tasks, deadlines, and mental workload."""

    def __init__(self, parent, colors, repository):
        super().__init__(parent, fg_color="transparent")
        self.colors = colors
        self.repository = repository
        self.create_widgets()
        self.refresh_dashboard()

    def create_widgets(self):
        # Welcome banner inspired by the supplied AuraPlan reference.
        self.welcome_card = ctk.CTkFrame(
            self, fg_color=self.colors["header"], corner_radius=16, height=132
        )
        self.welcome_card.pack(fill="x", pady=(4, 14))
        self.welcome_card.pack_propagate(False)

        self.date_label = ctk.CTkLabel(
            self.welcome_card, text="", font=("Segoe UI", 10, "bold"),
            text_color="#C8DED0"
        )
        self.date_label.pack(anchor="w", padx=20, pady=(16, 3))

        self.greeting_label = ctk.CTkLabel(
            self.welcome_card, text="", font=("Segoe UI", 27, "bold"),
            text_color="#FFFFFF"
        )
        self.greeting_label.pack(anchor="w", padx=20, pady=(0, 1))

        self.energy_label = ctk.CTkLabel(
            self.welcome_card, text="Energy  ·  Medium",
            font=("Segoe UI", 12, "bold"), text_color="#8FD3A8"
        )
        self.energy_label.pack(anchor="w", padx=20, pady=(0, 12))
        self.refresh_welcome()

        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", pady=4)
        for column in range(3):
            self.cards_frame.grid_columnconfigure(column, weight=1)

        self.stat_labels = {}
        for index, (key, heading) in enumerate([
            ("total", "Total Tasks"),
            ("completed", "Completed"),
            ("pending", "Pending"),
        ]):
            card = ctk.CTkFrame(
                self.cards_frame, fg_color=self.colors["surface"],
                corner_radius=14, height=112
            )
            card.grid(row=0, column=index, padx=6, sticky="nsew")
            card.grid_propagate(False)
            ctk.CTkLabel(
                card, text=heading, font=("Segoe UI", 13),
                text_color=self.colors["muted"]
            ).pack(anchor="w", padx=16, pady=(14, 2))
            value = ctk.CTkLabel(
                card, text="0", font=("Segoe UI", 28, "bold"),
                text_color=self.colors["text"]
            )
            value.pack(anchor="w", padx=16)
            self.stat_labels[key] = value

        overview = ctk.CTkFrame(
            self, fg_color=self.colors["surface"], corner_radius=14
        )
        overview.pack(fill="x", pady=(12, 10))
        ctk.CTkLabel(
            overview, text="Workload Overview",
            font=("Segoe UI", 17, "bold"), text_color=self.colors["text"]
        ).pack(anchor="w", padx=18, pady=(13, 7))

        self.today_label = ctk.CTkLabel(
            overview, text="Due today: 0",
            font=("Segoe UI", 12, "bold"), text_color=self.colors["primary"]
        )
        self.today_label.pack(anchor="w", padx=18, pady=(0, 5))

        self.load_label = ctk.CTkLabel(
            overview, text="High load: 0   •   Medium load: 0   •   Low load: 0",
            font=("Segoe UI", 12), text_color=self.colors["muted"]
        )
        self.load_label.pack(anchor="w", padx=18, pady=(0, 13))

        upcoming_card = ctk.CTkFrame(
            self, fg_color=self.colors["surface"], corner_radius=14
        )
        upcoming_card.pack(fill="both", expand=True, pady=(0, 5))

        header = ctk.CTkFrame(upcoming_card, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(13, 6))
        ctk.CTkLabel(
            header, text="Today's Tasks & Upcoming Deadlines",
            font=("Segoe UI", 17, "bold"), text_color=self.colors["text"]
        ).pack(side="left")
        ctk.CTkButton(
            header, text="Refresh", width=82, height=29,
            command=self.refresh_dashboard
        ).pack(side="right")

        self.upcoming_container = ctk.CTkScrollableFrame(
            upcoming_card, fg_color="transparent"
        )
        self.upcoming_container.pack(fill="both", expand=True, padx=12, pady=6)

    def refresh_welcome(self):
        """Refresh the date and time-based greeting shown on the dashboard."""
        now = datetime.now()
        hour = now.hour
        if 5 <= hour < 12:
            greeting = "Good morning"
        elif 12 <= hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        self.date_label.configure(
            text=f"{now.strftime('%A').upper()}, {now.strftime('%B').upper()} {now.day}"
        )
        self.greeting_label.configure(text=greeting)

    @staticmethod
    def _deadline(value):
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone().replace(tzinfo=None)
            return parsed
        except (TypeError, ValueError):
            return None

    def refresh_dashboard(self):
        try:
            tasks = self.repository.list_tasks()
        except Exception as exc:
            for label in self.stat_labels.values():
                label.configure(text="!")
            self.today_label.configure(text=f"Could not load tasks: {exc}")
            return

        completed = [t for t in tasks if t.status == "completed"]
        pending = [t for t in tasks if t.status not in ("completed", "cancelled")]
        self.stat_labels["total"].configure(text=str(len(tasks)))
        self.stat_labels["completed"].configure(text=str(len(completed)))
        self.stat_labels["pending"].configure(text=str(len(pending)))

        load_counts = {"high": 0, "medium": 0, "low": 0}
        for task in pending:
            level = str(task.load_level or "low").casefold()
            if level in load_counts:
                load_counts[level] += 1
        self.load_label.configure(
            text=(f"High load: {load_counts['high']}   •   "
                  f"Medium load: {load_counts['medium']}   •   "
                  f"Low load: {load_counts['low']}")
        )

        now = datetime.now().astimezone().replace(tzinfo=None)
        today = now.date()
        dated = [(self._deadline(t.deadline), t) for t in pending]
        dated = [(dt, t) for dt, t in dated if dt is not None]
        due_today = sum(1 for dt, _ in dated if dt.date() == today)
        self.today_label.configure(text=f"Due today: {due_today}")

        for widget in self.upcoming_container.winfo_children():
            widget.destroy()

        dated.sort(key=lambda item: item[0])
        todays = [(dt, t) for dt, t in dated if dt.date() == today]
        future = [(dt, t) for dt, t in dated if dt.date() > today]
        overdue = [(dt, t) for dt, t in dated if dt.date() < today]
        display = overdue[:3] + todays + future[:8]
        if not display:
            ctk.CTkLabel(
                self.upcoming_container,
                text="No dated tasks yet. Add a deadline from the Tasks page.",
                text_color=self.colors["muted"]
            ).pack(pady=22)
            return

        for deadline, task in display[:12]:
            card = ctk.CTkFrame(
                self.upcoming_container, fg_color=self.colors["surface_alt"],
                corner_radius=9
            )
            card.pack(fill="x", pady=3, padx=3)
            ctk.CTkLabel(
                card, text=task.title, font=("Segoe UI", 13, "bold"),
                text_color=self.colors["text"]
            ).pack(anchor="w", padx=12, pady=(7, 1))
            label = "Overdue" if deadline.date() < today else (
                "Today" if deadline.date() == today else deadline.strftime("%d %b %Y")
            )
            ctk.CTkLabel(
                card,
                text=(f"{label}  •  {deadline.strftime('%I:%M %p')}  •  "
                      f"{task.estimated_minutes} min  •  "
                      f"{task.load_level.title()} load"),
                font=("Segoe UI", 11), text_color=self.colors["muted"]
            ).pack(anchor="w", padx=12, pady=(0, 7))

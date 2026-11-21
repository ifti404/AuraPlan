import sys
from pathlib import Path

import customtkinter as ctk
from tkinter import messagebox

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from scheduler import generate_schedule


class SchedulePage(ctk.CTkFrame):
    """Generate an explainable daily plan from pending tasks and current energy."""

    def __init__(self, parent, colors, repository):
        super().__init__(parent, fg_color="transparent")
        self.colors = colors
        self.repository = repository
        self.last_result = None
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(
            self, text="Smart Schedule", font=("Segoe UI", 28, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", pady=(10, 5))
        ctk.CTkLabel(
            self, text="Generate a plan based on your available time and energy.",
            font=("Segoe UI", 14), text_color=self.colors["muted"]
        ).pack(anchor="w", pady=(0, 14))

        controls = ctk.CTkFrame(self, fg_color=self.colors["surface"], corner_radius=14)
        controls.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            controls, text="Available study time (minutes)",
            text_color=self.colors["text"]
        ).pack(anchor="w", padx=16, pady=(12, 4))
        self.available_time = ctk.CTkEntry(
            controls, height=36, placeholder_text="Example: 180"
        )
        self.available_time.insert(0, "180")
        self.available_time.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(
            controls, text="Current energy level", text_color=self.colors["text"]
        ).pack(anchor="w", padx=16, pady=(8, 4))
        self.energy = ctk.CTkOptionMenu(
            controls, values=["Low", "Medium", "High"], height=34
        )
        self.energy.set("Medium")
        self.energy.pack(anchor="w", padx=16, pady=4)

        action_row = ctk.CTkFrame(controls, fg_color="transparent")
        action_row.pack(anchor="w", padx=16, pady=(8, 13))
        ctk.CTkButton(
            action_row, text="Generate Schedule", height=36,
            command=self.generate
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            action_row, text="Refresh Plan", height=36,
            fg_color=self.colors["surface_alt"], text_color=self.colors["text"],
            command=self.generate
        ).pack(side="left")

        self.result_card = ctk.CTkFrame(
            self, fg_color=self.colors["surface"], corner_radius=14
        )
        self.result_card.pack(fill="both", expand=True)
        ctk.CTkLabel(
            self.result_card, text="Today's Plan",
            font=("Segoe UI", 18, "bold"), text_color=self.colors["text"]
        ).pack(anchor="w", padx=18, pady=(13, 5))
        self.result_container = ctk.CTkScrollableFrame(
            self.result_card, fg_color="transparent"
        )
        self.result_container.pack(fill="both", expand=True, padx=10, pady=6)
        self.show_message(
            "Set your available time and energy, then generate your schedule."
        )

    def show_message(self, message):
        for widget in self.result_container.winfo_children():
            widget.destroy()
        if message:
            ctk.CTkLabel(
                self.result_container, text=message,
                text_color=self.colors["muted"], wraplength=680
            ).pack(anchor="w", padx=10, pady=14)

    def _section(self, heading):
        ctk.CTkLabel(
            self.result_container, text=heading,
            font=("Segoe UI", 14, "bold"), text_color=self.colors["text"]
        ).pack(anchor="w", padx=7, pady=(10, 4))

    def generate(self):
        time_text = self.available_time.get().strip()
        if not time_text.isdigit() or int(time_text) <= 0:
            messagebox.showwarning(
                "Invalid time", "Enter available time as a positive number of minutes.",
                parent=self
            )
            return

        energy_value = {"Low": 2, "Medium": 3, "High": 5}.get(self.energy.get(), 3)
        try:
            tasks = self.repository.list_tasks(include_completed=False)
            if not tasks:
                self.last_result = None
                self.show_message("No pending tasks found. Add tasks first.")
                return
            result = generate_schedule(
                tasks, available_minutes=int(time_text), energy=energy_value
            )
        except Exception as exc:
            messagebox.showerror("Schedule error", str(exc), parent=self)
            return

        self.last_result = result
        self.show_message("")
        scheduled = result["scheduled"]
        deferred = result["deferred"]
        at_risk_ids = {item.get("id") for item in result.get("at_risk", [])}

        if scheduled:
            self._section("Recommended order")
            for index, task in enumerate(scheduled, start=1):
                card = ctk.CTkFrame(
                    self.result_container, fg_color=self.colors["surface_alt"],
                    corner_radius=9
                )
                card.pack(fill="x", pady=3, padx=3)
                title_text = f"{index}. {task['title']}"
                if task.get("partial"):
                    title_text += "  •  PARTIAL SESSION"
                ctk.CTkLabel(
                    card, text=title_text, font=("Segoe UI", 13, "bold"),
                    text_color=self.colors["text"]
                ).pack(anchor="w", padx=12, pady=(8, 2))
                ctk.CTkLabel(
                    card,
                    text=(f"Start after {task['start_offset_minutes']} min  •  "
                          f"Work: {task['scheduled_minutes']} min  •  "
                          f"Load: {task.get('load_level', 'N/A').title()}"),
                    font=("Segoe UI", 11), text_color=self.colors["muted"]
                ).pack(anchor="w", padx=12, pady=(0, 3))
                if task.get("reason"):
                    ctk.CTkLabel(
                        card, text=task["reason"], font=("Segoe UI", 11),
                        text_color=self.colors["muted"], wraplength=680,
                        justify="left"
                    ).pack(anchor="w", padx=12, pady=(0, 8))
        else:
            self._section("Recommended order")
            ctk.CTkLabel(
                self.result_container,
                text="No task fits the available time. Increase your time budget.",
                text_color=self.colors["muted"]
            ).pack(anchor="w", padx=8)

        ctk.CTkLabel(
            self.result_container,
            text=(f"Scheduled: {len(scheduled)}  •  Deferred: {len(deferred)}  •  "
                  f"Unused time: {result['remaining_minutes']} min"),
            font=("Segoe UI", 12, "bold"), text_color=self.colors["primary"]
        ).pack(anchor="w", padx=8, pady=10)

        if deferred:
            self._section("Not scheduled")
            for task in deferred:
                ctk.CTkLabel(
                    self.result_container,
                    text=f"• {task['title']} — {task.get('estimated_minutes', 0)} min",
                    text_color=self.colors["muted"]
                ).pack(anchor="w", padx=12, pady=2)

        if result.get("at_risk"):
            self._section("Deadline at risk")
            for task in result["at_risk"]:
                ctk.CTkLabel(
                    self.result_container,
                    text=f"⚠ {task['title']} — {task.get('reason', 'Not fully scheduled')}",
                    text_color=self.colors["warning"], wraplength=680,
                    justify="left"
                ).pack(anchor="w", padx=12, pady=2)

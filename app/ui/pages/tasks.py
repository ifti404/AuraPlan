from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox


class TasksPage(ctk.CTkFrame):
    """Create, edit, complete, and delete tasks using the local repository."""

    def __init__(self, parent, colors, repository):
        super().__init__(parent, fg_color="transparent")
        self.colors = colors
        self.repository = repository
        self.create_widgets()
        self.refresh_tasks()

    def create_widgets(self):
        ctk.CTkLabel(
            self, text="My Tasks", font=("Segoe UI", 28, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", pady=(10, 5))
        ctk.CTkLabel(
            self, text="Create, organize and track your tasks.",
            font=("Segoe UI", 14), text_color=self.colors["muted"]
        ).pack(anchor="w", pady=(0, 12))

        form = ctk.CTkFrame(self, fg_color=self.colors["surface"], corner_radius=14)
        form.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            form, text="Add New Task", font=("Segoe UI", 18, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", padx=18, pady=(12, 6))

        self.task_title = ctk.CTkEntry(form, placeholder_text="Task title", height=36)
        self.task_title.pack(fill="x", padx=18, pady=4)
        self.description = ctk.CTkEntry(
            form, placeholder_text="Description (optional)", height=36
        )
        self.description.pack(fill="x", padx=18, pady=4)
        self.deadline = ctk.CTkEntry(
            form, placeholder_text="Deadline: YYYY-MM-DD or YYYY-MM-DD HH:MM",
            height=36
        )
        self.deadline.pack(fill="x", padx=18, pady=4)
        self.duration = ctk.CTkEntry(
            form, placeholder_text="Estimated duration in minutes", height=36
        )
        self.duration.pack(fill="x", padx=18, pady=4)
        self.load_level = ctk.CTkOptionMenu(
            form, values=["Low", "Medium", "High"], height=34
        )
        self.load_level.set("Medium")
        self.load_level.pack(anchor="w", padx=18, pady=5)
        ctk.CTkButton(
            form, text="+ Add Task", height=38, command=self.add_task
        ).pack(anchor="w", padx=18, pady=(3, 13))

        list_card = ctk.CTkFrame(self, fg_color=self.colors["surface"], corner_radius=14)
        list_card.pack(fill="both", expand=True)
        header = ctk.CTkFrame(list_card, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(12, 5))
        ctk.CTkLabel(
            header, text="Task List", font=("Segoe UI", 18, "bold"),
            text_color=self.colors["text"]
        ).pack(side="left")
        ctk.CTkButton(
            header, text="Refresh", width=82, height=29,
            command=self.refresh_tasks
        ).pack(side="right")
        self.task_container = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.task_container.pack(fill="both", expand=True, padx=10, pady=6)

    @staticmethod
    def _parse_deadline(text):
        text = text.strip()
        if not text:
            return None
        try:
            if len(text) == 10:
                value = datetime.strptime(text, "%Y-%m-%d").replace(
                    hour=23, minute=59
                )
            else:
                value = datetime.fromisoformat(text)
            if value.tzinfo is None:
                value = value.astimezone()
            return value.isoformat()
        except ValueError as exc:
            raise ValueError(
                "Use YYYY-MM-DD or YYYY-MM-DD HH:MM for the deadline."
            ) from exc

    @staticmethod
    def _validate_duration(text):
        if not text.isdigit() or int(text) <= 0:
            raise ValueError("Estimated duration must be a positive number of minutes.")
        return int(text)

    def _form_values(self):
        title = self.task_title.get().strip()
        if not title:
            raise ValueError("Please enter a task title.")
        return {
            "title": title,
            "description": self.description.get().strip(),
            "deadline": self._parse_deadline(self.deadline.get()),
            "estimated_minutes": self._validate_duration(self.duration.get().strip()),
            "load_level": self.load_level.get().casefold(),
        }

    def add_task(self):
        try:
            values = self._form_values()
            self.repository.create_task(**values, status="pending")
        except ValueError as exc:
            messagebox.showwarning("Check task details", str(exc), parent=self)
            return
        except Exception as exc:
            messagebox.showerror("Could not save task", str(exc), parent=self)
            return

        for field in (self.task_title, self.description, self.deadline, self.duration):
            field.delete(0, "end")
        self.load_level.set("Medium")
        self.refresh_tasks()

    def refresh_tasks(self):
        for widget in self.task_container.winfo_children():
            widget.destroy()
        try:
            tasks = self.repository.list_tasks()
        except Exception as exc:
            ctk.CTkLabel(
                self.task_container, text=f"Could not load tasks: {exc}",
                text_color=self.colors["danger"]
            ).pack(pady=15)
            return
        if not tasks:
            ctk.CTkLabel(
                self.task_container, text="No tasks yet. Add your first task above.",
                text_color=self.colors["muted"]
            ).pack(pady=22)
            return
        for task in reversed(tasks):
            self.display_task(task)

    def display_task(self, task):
        card = ctk.CTkFrame(
            self.task_container, fg_color=self.colors["surface_alt"], corner_radius=10
        )
        card.pack(fill="x", pady=4, padx=3)
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(8, 2))
        ctk.CTkLabel(
            top, text=task.title, font=("Segoe UI", 14, "bold"),
            text_color=self.colors["text"]
        ).pack(side="left", anchor="w")
        ctk.CTkLabel(
            top, text=task.status.replace("_", " ").title(),
            text_color=(self.colors["success"] if task.status == "completed"
                        else self.colors["muted"])
        ).pack(side="right")
        deadline = task.deadline or "Not set"
        if deadline != "Not set":
            try:
                parsed = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
                deadline = parsed.astimezone().strftime("%d %b %Y, %I:%M %p") if parsed.tzinfo else parsed.strftime("%d %b %Y, %I:%M %p")
            except ValueError:
                deadline = deadline[:16]
        ctk.CTkLabel(
            card,
            text=(f"Deadline: {deadline}   |   {task.estimated_minutes} min   |   "
                  f"{task.load_level.title()} load"),
            font=("Segoe UI", 11), text_color=self.colors["muted"]
        ).pack(anchor="w", padx=12, pady=(1, 5))
        if task.description:
            ctk.CTkLabel(
                card, text=task.description, font=("Segoe UI", 11),
                text_color=self.colors["muted"], wraplength=680, justify="left"
            ).pack(anchor="w", padx=12, pady=(0, 5))
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(anchor="e", padx=8, pady=(0, 7))
        ctk.CTkButton(
            actions, text="Edit", width=65, height=28,
            command=lambda item=task: self.edit_task(item)
        ).pack(side="left", padx=3)
        if task.status != "completed":
            ctk.CTkButton(
                actions, text="Complete", width=82, height=28,
                fg_color=self.colors["success"],
                command=lambda task_id=task.id: self.complete_task(task_id)
            ).pack(side="left", padx=3)
        else:
            ctk.CTkButton(
                actions, text="Reopen", width=72, height=28,
                command=lambda task_id=task.id: self.reopen_task(task_id)
            ).pack(side="left", padx=3)
        ctk.CTkButton(
            actions, text="Delete", width=68, height=28,
            fg_color=self.colors["danger"], hover_color="#B91C1C",
            command=lambda task_id=task.id: self.delete_task(task_id)
        ).pack(side="left", padx=3)

    def edit_task(self, task):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Task")
        dialog.geometry("480x470")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=self.colors["background"])

        ctk.CTkLabel(
            dialog, text="Edit Task", font=("Segoe UI", 22, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", padx=22, pady=(18, 10))

        title = ctk.CTkEntry(dialog, height=36, placeholder_text="Task title")
        title.pack(fill="x", padx=22, pady=5)
        title.insert(0, task.title)
        description = ctk.CTkEntry(
            dialog, height=36, placeholder_text="Description (optional)"
        )
        description.pack(fill="x", padx=22, pady=5)
        description.insert(0, task.description or "")
        deadline = ctk.CTkEntry(
            dialog, height=36, placeholder_text="YYYY-MM-DD or YYYY-MM-DD HH:MM"
        )
        deadline.pack(fill="x", padx=22, pady=5)
        if task.deadline:
            try:
                dt = datetime.fromisoformat(task.deadline.replace("Z", "+00:00"))
                deadline.insert(0, dt.astimezone().strftime("%Y-%m-%d %H:%M") if dt.tzinfo else dt.strftime("%Y-%m-%d %H:%M"))
            except ValueError:
                deadline.insert(0, task.deadline)
        duration = ctk.CTkEntry(dialog, height=36, placeholder_text="Duration in minutes")
        duration.pack(fill="x", padx=22, pady=5)
        duration.insert(0, str(task.estimated_minutes))
        load = ctk.CTkOptionMenu(dialog, values=["Low", "Medium", "High"], height=34)
        load.set(task.load_level.title())
        load.pack(anchor="w", padx=22, pady=6)

        def save():
            try:
                new_title = title.get().strip()
                if not new_title:
                    raise ValueError("Task title cannot be empty.")
                changes = {
                    "title": new_title,
                    "description": description.get().strip(),
                    "deadline": self._parse_deadline(deadline.get()),
                    "estimated_minutes": self._validate_duration(duration.get().strip()),
                    "load_level": load.get().casefold(),
                }
                updated = self.repository.update_task(task.id, **changes)
                if updated is None:
                    raise ValueError("This task no longer exists.")
            except ValueError as exc:
                messagebox.showwarning("Check task details", str(exc), parent=dialog)
                return
            except Exception as exc:
                messagebox.showerror("Could not update task", str(exc), parent=dialog)
                return
            dialog.destroy()
            self.refresh_tasks()

        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.pack(fill="x", padx=22, pady=(12, 18))
        ctk.CTkButton(
            buttons, text="Save Changes", command=save, height=38
        ).pack(side="left")
        ctk.CTkButton(
            buttons, text="Cancel", command=dialog.destroy, height=38,
            fg_color=self.colors["surface_alt"], text_color=self.colors["text"]
        ).pack(side="left", padx=8)

    def complete_task(self, task_id):
        try:
            self.repository.update_task(task_id, status="completed")
            self.refresh_tasks()
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)

    def reopen_task(self, task_id):
        try:
            self.repository.update_task(task_id, status="pending")
            self.refresh_tasks()
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)

    def delete_task(self, task_id):
        if not messagebox.askyesno(
            "Delete task", "Are you sure you want to delete this task?", parent=self
        ):
            return
        try:
            self.repository.delete_task(task_id)
            self.refresh_tasks()
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)

"""AuraPlan dashboard pages for today's plan, tasks, and the coming week."""
from datetime import datetime

from app.voices.voice_session import VoiceSession
from planner import plan_week
from scheduler import generate_schedule
from task_form import TaskForm
from ui_compat import (COLORS, FONT_FAMILY, CUSTOM, button, energy_selector, entry,
                       frame, get_theme_mode, label, messagebox, option_menu, brand_mark_image,
                       scrollable, tk)


class Dashboard:
    def __init__(self, parent, repository, energy_level=None, voice_input=None,
                 on_toggle_theme=None, theme_icon=None, brand_icon=None):
        self.parent, self.repo = parent, repository
        self.on_toggle_theme = on_toggle_theme
        self.theme_icon = theme_icon
        self.brand_icon = brand_icon
        self.energy = energy_level or tk.StringVar(value="Medium")
        self.voice_input = voice_input
        self.voice_session = None
        self.view = "today"
        self.minutes = tk.StringVar(value="180")
        self._minutes_entry = None
        self._minutes_commit_after = None
        self._refresh_after = None
        self.search = tk.StringVar()
        self.task_filter = tk.StringVar(value="All tasks")
        self.panel = frame(parent, fg_color="transparent")
        self._build()
        self._disposed = False
        self._energy_trace_id = self.energy.trace_add("write", self._energy_changed)
        self.refresh()

    def _build(self):
        header = frame(self.panel, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(26, 18))
        if self.brand_icon is not None:
            label(header, image=self.brand_icon, text="", width=48, height=48).pack(
                side="left", padx=(0, 12), anchor="center")
        title_group = frame(header, fg_color="transparent")
        title_group.pack(side="left", fill="x", expand=True)
        label(title_group, datetime.now().strftime("%A, %B %d").upper(),
              font=(FONT_FAMILY, 12, "bold"), text_color=COLORS["muted"]).pack(anchor="w")
        label(title_group, self._greeting(), font=(FONT_FAMILY, 30, "bold")).pack(anchor="w", pady=(3, 0))
        self.energy_badge = label(title_group, "Energy · Medium",
                                  font=(FONT_FAMILY, 13, "bold"),
                                  text_color=COLORS["leaf"] if get_theme_mode() == "dark"
                                  else COLORS["primary"])
        self.energy_badge.pack(anchor="w", pady=(3, 0))
        button(header, "+  Add task", self.add_task, width=130, height=40).pack(side="right", anchor="center")
        icon_text = "" if self.theme_icon is not None else (
            "☾" if get_theme_mode() == "light" else "☀")
        self.theme_button = button(
            header, icon_text, self.on_toggle_theme,
            width=44 if self.theme_icon is not None or icon_text else 132,
            height=40, image=self.theme_icon,
            fg_color="transparent",
            hover_color=COLORS["surface_alt"],
            text_color=COLORS["text"],
        )
        self.theme_button.pack(side="right", anchor="center", padx=(0, 9))

        self.body = frame(self.panel, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=30, pady=(0, 14))
        self._build_voice_bar()
        if self.voice_input is None:
            self.voice_button.configure(state="disabled")

    def _build_voice_bar(self):
        panel = frame(self.panel, fg_color=COLORS["mint"], corner_radius=18)
        panel.pack(fill="x", padx=30, pady=(0, 22))
        row = frame(panel, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(12, 6))
        label(row, "QUICK CAPTURE", font=(FONT_FAMILY, 12, "bold"),
              text_color=COLORS["forest"]).pack(side="left", padx=(0, 12))
        self.voice_text = tk.StringVar()
        entry(row, variable=self.voice_text, placeholder="Type a task or use your voice…",
              height=36).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.voice_button = button(row, "Start recording", self.toggle_voice, width=140, height=36)
        self.voice_button.pack(side="left", padx=(0, 8))
        button(row, "Add task", self.review_voice, width=90, height=36).pack(side="left")
        self.voice_status = label(panel, "Offline voice input · review your words before adding a task",
                                  font=(FONT_FAMILY, 12), text_color=COLORS["forest"])
        self.voice_status.pack(anchor="w", padx=16, pady=(0, 10))

    def show(self):
        self.panel.pack(fill="both", expand=True)

    def hide(self):
        self.panel.pack_forget()

    def dispose(self):
        """Detach model callbacks before the themed widget tree is destroyed."""
        self._disposed = True
        self._cancel_minutes_commit()
        self._cancel_scheduled_refresh()
        if self._energy_trace_id is not None:
            try:
                self.energy.trace_remove("write", self._energy_trace_id)
            except tk.TclError:
                pass
            self._energy_trace_id = None

    def show_view(self, view):
        if view not in {"today", "tasks", "week"}:
            view = "today"
        self.view = view
        self.schedule_refresh()

    def _clear_body(self):
        for child in self.body.winfo_children():
            child.destroy()

    def refresh(self, show_risk_popup=False):
        if self._disposed:
            return
        self._cancel_minutes_commit()
        self.energy_badge.configure(text=f"Energy · {self.energy.get()}")
        tasks = self.repo.list_tasks()
        pending = [t for t in tasks if t.status not in {"completed", "cancelled"}]
        completed = [t for t in tasks if t.status == "completed"]
        if not self.minutes.get().isdigit():
            self.minutes.set("180")
        energy = {"Low": 1, "Medium": 3, "High": 5}.get(self.energy.get(), 3)
        try:
            daily_plan = generate_schedule(pending, available_minutes=int(self.minutes.get()), energy=energy)
            week_plan = plan_week(pending, daily_minutes=int(self.minutes.get()), energy=energy)
        except Exception as exc:
            self._clear_body()
            label(self.body, f"Could not prepare your plan: {exc}", text_color=COLORS["danger"]).pack(anchor="w")
            return
        self.deadline_risks = [("Overdue", item) for item in week_plan["late"]]
        self.deadline_risks.extend(("At risk", item) for item in week_plan["at_risk"])
        self._clear_body()
        if self.view == "today":
            self._render_today(pending, completed, daily_plan)
        elif self.view == "tasks":
            self._render_tasks(tasks)
        else:
            self._render_week(week_plan)

    def schedule_refresh(self, show_risk_popup=False):
        """Redraw after CustomTkinter's delayed click/focus callbacks finish."""
        if self._disposed:
            return
        self._cancel_scheduled_refresh()
        try:
            self._refresh_after = self.parent.after(
                250, lambda: self._run_scheduled_refresh(show_risk_popup)
            )
        except tk.TclError:
            self._refresh_after = None

    def _run_scheduled_refresh(self, show_risk_popup):
        self._refresh_after = None
        self.refresh(show_risk_popup=show_risk_popup)

    def _cancel_scheduled_refresh(self):
        callback_id = self._refresh_after
        self._refresh_after = None
        if callback_id is not None:
            try:
                self.parent.after_cancel(callback_id)
            except tk.TclError:
                pass

    def _render_today(self, pending, completed, plan):
        if self.deadline_risks:
            alert = frame(self.body, fg_color=COLORS["danger_surface"])
            alert.pack(fill="x", pady=(0, 12))
            label(alert, "Deadline risks", font=(FONT_FAMILY, 14, "bold"),
                  text_color=COLORS["danger"]).pack(anchor="w", padx=14, pady=(10, 3))
            label(alert, "\n".join(
                f"{category}: {item['title']} — {item['reason']}"
                for category, item in self.deadline_risks),
                font=(FONT_FAMILY, 12), text_color=COLORS["danger"], wraplength=850,
                justify="left").pack(anchor="w", padx=14, pady=(0, 10))
        stats = frame(self.body, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 16))
        deadlines = sorted((t for t in pending if t.deadline), key=lambda t: t.deadline)
        values = (("OPEN TASKS", str(len(pending))), ("COMPLETED", str(len(completed))),
                  ("NEXT DEADLINE", self._format_due(deadlines[0].deadline) if deadlines else "None"))
        for heading, value in values:
            card = frame(stats, fg_color=COLORS["surface"], height=78)
            card.pack(side="left", fill="x", expand=True, padx=(0, 10))
            label(card, heading, font=(FONT_FAMILY, 11, "bold"), text_color=COLORS["muted"]).pack(
                anchor="w", padx=14, pady=(12, 2))
            label(card, value, font=(FONT_FAMILY, 19, "bold")).pack(anchor="w", padx=14)

        plan_panel = frame(self.body, fg_color=COLORS["surface"])
        plan_panel.pack(fill="both", expand=True)
        controls = frame(plan_panel, fg_color="transparent")
        controls.pack(fill="x", padx=18, pady=(14, 10))
        title = frame(controls, fg_color="transparent")
        title.pack(side="left", fill="x", expand=True)
        label(title, "Today's focus", font=(FONT_FAMILY, 24, "bold")).pack(anchor="w")
        label(title, "Study time and mental load for today's plan.",
              font=(FONT_FAMILY, 13), text_color=COLORS["muted"]).pack(anchor="w", pady=(2, 0))

        settings = frame(plan_panel, fg_color=COLORS["surface_alt"])
        settings.pack(fill="x", padx=18, pady=(0, 12))
        label(settings, "PLAN SETTINGS", font=(FONT_FAMILY, 11, "bold"),
              text_color=COLORS["muted"]).pack(anchor="w", padx=14, pady=(10, 5))
        settings_row = frame(settings, fg_color="transparent")
        settings_row.pack(fill="x", padx=12, pady=(0, 12))
        energy_group = frame(settings_row, fg_color="transparent")
        energy_group.pack(side="left", fill="x", expand=True, padx=(0, 14))
        label(energy_group, "Current energy", font=(FONT_FAMILY, 12, "bold")).pack(anchor="w", pady=(0, 5))
        energy_selector(energy_group, ["Low", "Medium", "High"], self.energy).pack(fill="x")

        time_group = frame(settings_row, fg_color="transparent")
        time_group.pack(side="left", fill="x", expand=True)
        label(time_group, "Available study time", font=(FONT_FAMILY, 12, "bold")).pack(anchor="w", pady=(0, 5))
        time_controls = frame(time_group, fg_color="transparent")
        time_controls.pack(fill="x")
        self._minutes_entry = entry(time_controls, variable=self.minutes, width=96, height=40)
        self._minutes_entry.pack(side="left", padx=(0, 6))
        self._minutes_entry.bind("<FocusOut>", self._schedule_minutes_commit)
        self._minutes_entry.bind("<Return>", self._refresh_from_controls)
        label(time_controls, "min", font=(FONT_FAMILY, 13, "bold"), text_color=COLORS["muted"]).pack(side="left")
        button(time_controls, "Refresh plan", self._refresh_from_controls,
               width=112, height=40).pack(side="left", padx=(12, 0))
        line = frame(plan_panel, height=1, fg_color=COLORS["border"])
        line.pack(fill="x", padx=16)

        scheduled_minutes = sum(
            int(item.get("scheduled_minutes", item.get("estimated_minutes", 0)) or 0)
            for item in plan["scheduled"]
        )
        load_counts = {"high": 0, "medium": 0, "low": 0}
        for item in plan["scheduled"]:
            level = str(item.get("load_level", "medium")).casefold()
            if level in load_counts:
                load_counts[level] += 1
        overview = frame(plan_panel, fg_color="transparent")
        overview.pack(fill="x", padx=16, pady=(10, 2))
        time_card = frame(overview, fg_color=COLORS["surface_alt"], height=88)
        time_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        time_card.pack_propagate(False)
        label(time_card, "STUDY TIME PLANNED", font=(FONT_FAMILY, 11, "bold"),
              text_color=COLORS["muted"]).pack(anchor="w", padx=14, pady=(10, 0))
        label(time_card, f"{scheduled_minutes} / {plan['available_minutes']} min",
              font=(FONT_FAMILY, 22, "bold"),
              text_color=COLORS["leaf"] if get_theme_mode() == "dark"
              else COLORS["primary"]).pack(anchor="w", padx=14, pady=(0, 8))

        load_card = frame(overview, fg_color=COLORS["surface_alt"], height=88)
        load_card.pack(side="left", fill="both", expand=True, padx=(8, 0))
        load_card.pack_propagate(False)
        load_header = frame(load_card, fg_color="transparent")
        load_header.pack(fill="x", padx=12, pady=(7, 0))
        label(load_header, "MENTAL LOAD", font=(FONT_FAMILY, 11, "bold"),
              text_color=COLORS["muted"]).pack(side="left")
        levels = frame(load_card, fg_color="transparent")
        levels.pack(fill="x", padx=12, pady=(2, 7))
        for level, color in (("high", COLORS["forest"] if get_theme_mode() == "light" else COLORS["mint"]),
                             ("medium", COLORS["warning"]),
                             ("low", COLORS["leaf"] if get_theme_mode() == "dark"
                              else COLORS["primary"])):
            cell = frame(levels, fg_color=COLORS["surface"])
            cell.pack(side="left", fill="both", expand=True, padx=(0, 5))
            label(cell, str(load_counts[level]), font=(FONT_FAMILY, 16, "bold"),
                  text_color=color).pack(anchor="center", pady=(3, 0))
            label(cell, f"{level.title()} load", font=(FONT_FAMILY, 10, "bold"),
                  text_color=COLORS["muted"]).pack(anchor="center", pady=(0, 3))

        box = scrollable(plan_panel)
        box.pack(fill="both", expand=True, padx=12, pady=8)
        inner = box if CUSTOM else box.inner
        if not plan["scheduled"]:
            empty_message = ("No tasks fit in today's available study time. Review the deadline risks above or increase the time."
                             if self.deadline_risks else
                             "Your plan is clear. Add a task or increase today's study time.")
            label(inner, empty_message,
                  font=(FONT_FAMILY, 12), text_color=COLORS["muted"], wraplength=620,
                  justify="left").pack(anchor="w", padx=16, pady=20)
        for index, item in enumerate(plan["scheduled"], 1):
            task = next((t for t in pending if t.id == item.get("id")), None)
            if task:
                note = item.get("reason") or ""
                if item.get("partial"):
                    note = f"Short session · {item['scheduled_minutes']} of {task.estimated_minutes} min. {note}"
                self._task_card(inner, task, index, note=note,
                                minutes=item.get("scheduled_minutes"))
        if plan["deferred"]:
            label(inner, f"{len(plan['deferred'])} task(s) were moved to a later study block.",
                  font=(FONT_FAMILY, 12), text_color=COLORS["warning"]).pack(anchor="w", padx=14, pady=8)

    def _render_tasks(self, tasks):
        toolbar = frame(self.body, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 12))
        title = frame(toolbar, fg_color="transparent")
        title.pack(side="left", fill="x", expand=True)
        label(title, "Your tasks", font=(FONT_FAMILY, 22, "bold")).pack(anchor="w")
        label(title, "Search, update, or complete your academic work.",
              font=(FONT_FAMILY, 12), text_color=COLORS["muted"]).pack(anchor="w")
        search_entry = entry(toolbar, variable=self.search, placeholder="Search tasks", width=180,
                             height=36)
        search_entry.pack(side="right", padx=(8, 0))
        search_entry.bind("<Return>", lambda _event: self.schedule_refresh())
        button(toolbar, "Search", self.refresh, width=72, height=36).pack(side="right", padx=(8, 0))
        filter_menu = option_menu(toolbar, ["All tasks", "Pending", "Completed"], self.task_filter,
                                  command=lambda _value: self.schedule_refresh(), width=125, height=36)
        filter_menu.pack(side="right")
        if not CUSTOM:
            filter_menu.bind("<<ComboboxSelected>>", lambda _event: self.schedule_refresh())
        panel = frame(self.body, fg_color=COLORS["surface"])
        panel.pack(fill="both", expand=True)
        box = scrollable(panel)
        box.pack(fill="both", expand=True, padx=10, pady=10)
        inner = box if CUSTOM else box.inner
        query = self.search.get().strip().casefold()
        selected = self.task_filter.get()
        visible = [task for task in tasks
                   if (selected == "All tasks"
                       or selected == "Pending" and task.status not in {"completed", "cancelled"}
                       or selected == "Completed" and task.status == "completed")
                   and (not query or query in task.title.casefold()
                        or query in task.description.casefold())]
        if not visible:
            label(inner, "No matching tasks. Add a task or change your search/filter.",
                  font=(FONT_FAMILY, 12), text_color=COLORS["muted"]).pack(anchor="w", padx=14, pady=20)
        for index, task in enumerate(visible, 1):
            self._task_card(inner, task, index)

    def _render_week(self, week):
        header = frame(self.body, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))
        label(header, "7-day plan", font=(FONT_FAMILY, 22, "bold")).pack(anchor="w")
        label(header, "A flexible outline. Refresh today's available minutes on the Today page.",
              font=(FONT_FAMILY, 12), text_color=COLORS["muted"]).pack(anchor="w", pady=(2, 0))
        risks = week["late"] + week["at_risk"]
        if risks:
            alert = frame(self.body, fg_color=COLORS["danger_surface"])
            alert.pack(fill="x", pady=(0, 12))
            label(alert, "Deadline risks", font=(FONT_FAMILY, 14, "bold"),
                  text_color=COLORS["danger"]).pack(anchor="w", padx=14, pady=(10, 3))
            label(alert, "\n".join(f"• {item['title']} — {item['reason']}" for item in risks),
                  font=(FONT_FAMILY, 12), text_color=COLORS["danger"], wraplength=800,
                  justify="left").pack(anchor="w", padx=14, pady=(0, 10))
        panel = frame(self.body, fg_color=COLORS["surface"])
        panel.pack(fill="both", expand=True)
        box = scrollable(panel)
        box.pack(fill="both", expand=True, padx=10, pady=10)
        inner = box if CUSTOM else box.inner
        for day in week["days"]:
            day_card = frame(inner, fg_color=COLORS["surface_alt"])
            day_card.pack(fill="x", padx=5, pady=5)
            date_label = datetime.fromisoformat(day["date"]).strftime("%A · %B %d")
            head = frame(day_card, fg_color="transparent")
            head.pack(fill="x", padx=14, pady=(10, 5))
            label(head, date_label, font=(FONT_FAMILY, 14, "bold")).pack(side="left")
            label(head, f"{day['used_minutes']} / {day['available_minutes']} min",
                  font=(FONT_FAMILY, 14, "bold"),
                  text_color=COLORS["leaf"] if get_theme_mode() == "dark"
                  else COLORS["primary"]).pack(side="right")
            if day["blocks"]:
                for block in day["blocks"]:
                    label(day_card, f"•  {block['title']}    {block['minutes']} min",
                          font=(FONT_FAMILY, 12), text_color=COLORS["text"]).pack(
                              anchor="w", padx=16, pady=(0, 5))
            else:
                label(day_card, "No study blocks planned", font=(FONT_FAMILY, 12),
                      text_color=COLORS["muted"]).pack(anchor="w", padx=16, pady=(0, 10))

    def _task_card(self, parent, task, number, note="", minutes=None):
        card = frame(parent, fg_color=COLORS["surface_alt"])
        card.pack(fill="x", padx=5, pady=5)
        row = frame(card, fg_color="transparent")
        row.pack(fill="x", padx=13, pady=(10, 3))
        label(row, f"{number:02d}", font=(FONT_FAMILY, 11, "bold"), text_color=COLORS["muted"]).pack(side="left")
        label(row, task.title, font=(FONT_FAMILY, 14, "bold"), wraplength=560,
              justify="left").pack(side="left", padx=10, fill="x", expand=True)
        dark_mode = get_theme_mode() == "dark"
        load_color = {
            "low": COLORS["leaf"] if dark_mode else COLORS["primary"],
            "medium": COLORS["warning"],
            "high": COLORS["mint"] if dark_mode else COLORS["forest"],
        }.get(task.load_level.casefold(), COLORS["muted"])
        meta = frame(card, fg_color="transparent")
        meta.pack(fill="x", padx=38, pady=(0, 3))
        label(meta, f"{task.load_level.title()} load", font=(FONT_FAMILY, 12, "bold"),
              text_color=load_color).pack(side="left")
        label(meta, f"{minutes or task.estimated_minutes} min  ·  Due {self._format_due(task.deadline)}  ·  {task.status.replace('_', ' ').title()}",
              font=(FONT_FAMILY, 11), text_color=COLORS["muted"]).pack(side="left", padx=(9, 0))
        if note:
            label(card, note, font=(FONT_FAMILY, 12), text_color=COLORS["muted"],
                  wraplength=680, justify="left").pack(anchor="w", padx=38, pady=(2, 5))
        actions = frame(card, fg_color="transparent")
        actions.pack(fill="x", padx=37, pady=(2, 9))
        if task.status not in {"completed", "cancelled"}:
            button(actions, "Mark complete", lambda t=task: self.complete(t),
                   width=112, height=28).pack(side="left", padx=(0, 6))
        button(actions, "Edit", lambda t=task: self.edit_task(t), width=64,
               height=28).pack(side="left", padx=(0, 6))
        button(actions, "Delete", lambda t=task: self.delete_task(t), width=70,
               height=28, fg_color=COLORS["danger_surface"], hover_color=COLORS["danger"],
               text_color=COLORS["danger"]).pack(side="left")

    @staticmethod
    def _greeting():
        hour = datetime.now().hour
        return "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"

    @staticmethod
    def _format_due(value):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%b %d · %I:%M %p")
        except (ValueError, AttributeError):
            return value or "No deadline"

    def add_task(self):
        TaskForm(self.parent, self._save_task)

    def edit_task(self, task):
        TaskForm(self.parent, self._save_task, task=task)

    def _save_task(self, values, task):
        if task and task.id:
            self.repo.update_task(task.id, **values)
        else:
            self.repo.create_task(**values)
        self.schedule_refresh()

    def complete(self, task):
        self.repo.update_task(task.id, status="completed")
        self.schedule_refresh()

    def delete_task(self, task):
        if messagebox.askyesno("Delete task", f"Delete ‘{task.title}’?", parent=self.parent):
            self.repo.delete_task(task.id)
            self.schedule_refresh()

    def _energy_changed(self, *_args):
        if not self._disposed:
            self.schedule_refresh(show_risk_popup=True)

    def _schedule_minutes_commit(self, _event=None):
        """Replan when the user leaves the time field, after a short pause."""
        if self._disposed:
            return
        self._cancel_minutes_commit()
        try:
            self._minutes_commit_after = self.parent.after(250, self._commit_minutes)
        except tk.TclError:
            self._minutes_commit_after = None

    def _cancel_minutes_commit(self):
        callback_id = self._minutes_commit_after
        self._minutes_commit_after = None
        if callback_id is not None:
            try:
                self.parent.after_cancel(callback_id)
            except tk.TclError:
                pass

    def _commit_minutes(self):
        self._minutes_commit_after = None
        if self._disposed:
            return
        if not self.minutes.get().strip().isdigit():
            messagebox.showwarning(
                "Study time", "Enter available study time as a whole number of minutes.",
                parent=self.parent,
            )
            return
        self.refresh(show_risk_popup=True)

    def _refresh_from_controls(self, _event=None):
        self._cancel_minutes_commit()
        if not self.minutes.get().strip().isdigit():
            messagebox.showwarning(
                "Study time", "Enter available study time as a whole number of minutes.",
                parent=self.parent,
            )
            return "break"
        self.schedule_refresh(show_risk_popup=True)
        return "break"

    def set_voice_loading(self):
        self.voice_input = None
        self.voice_button.configure(state="disabled", text="Loading voice…")
        self.voice_status.configure(
            text="Loading the offline Vosk model · this large model takes about 20 seconds here; you can use AuraPlan while it loads"
        )

    def set_voice_ready(self, voice_input):
        self.voice_input = voice_input
        self.voice_button.configure(state="normal", text="Start recording")
        self.voice_status.configure(text="Voice ready · offline Vosk · review before adding")

    def toggle_voice(self):
        if self.voice_session is not None:
            self.voice_status.configure(text="Stopping and finishing speech recognition…")
            self.voice_button.configure(state="disabled", text="Finishing…")
            self.voice_session.stop()
            return
        if self.voice_input is None:
            return
        self.voice_button.configure(text="Stop recording")
        self.voice_status.configure(text="Opening microphone…")
        self.voice_session = VoiceSession(
            self.voice_input,
            on_started=lambda: self.parent.after(0, self._voice_started),
            on_finished=lambda text, error: self.parent.after(
                0, lambda: self._voice_finished(text, error)),
        )
        self.voice_session.start()

    def _voice_started(self):
        if self.voice_session is not None:
            self.voice_status.configure(text="Listening · press Stop recording when you're done")

    def _voice_finished(self, transcript, error):
        self.voice_session = None
        self.voice_button.configure(state="normal", text="Start recording")
        if error:
            self.voice_status.configure(text="Voice input failed · check microphone access")
            messagebox.showerror("Voice input", error, parent=self.parent)
        elif transcript:
            self.voice_text.set(transcript)
            self.voice_status.configure(text="Speech recognized · review the text before adding")
        else:
            self.voice_status.configure(text="No speech recognized · try again or type a task")

    def set_voice_unavailable(self, error):
        self.voice_button.configure(state="disabled", text="Voice unavailable")
        self.voice_status.configure(text=f"Voice input unavailable · {error}")

    def review_voice(self):
        phrase = self.voice_text.get().strip()
        if not phrase:
            messagebox.showinfo("Quick capture", "Enter or recognize a task first.", parent=self.parent)
            return
        TaskForm(self.parent, self._save_task, initial_title=phrase)

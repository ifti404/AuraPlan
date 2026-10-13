"""Add/edit task form dialog."""
import calendar
from datetime import date, datetime

from task_classifier import classify_task_detail
from ui_compat import (COLORS, FONT_FAMILY, CUSTOM, button, ctk, entry, frame,
                       get_theme_mode, label, messagebox, scrollable, option_menu,
                       tk, textbox)


class TaskForm:
    def __init__(self, parent, on_save, task=None, initial_title=""):
        self.on_save = on_save
        self.task = task
        self.window = ctk.CTkToplevel(parent) if CUSTOM else tk.Toplevel(parent)
        self.window.title("Edit task" if task else "Add a task")
        self.window.geometry("540x800")
        self.window.configure(fg_color=COLORS["background"]) if CUSTOM else self.window.configure(bg=COLORS["background"])
        self.window.transient(parent)
        self.window.grab_set()
        self.calendar_window = None
        self.clock_window = None
        self._calendar_render_after = None
        pad = 20
        body = scrollable(self.window)
        body.pack(fill="both", expand=True, padx=pad, pady=pad)
        content = body if CUSTOM else body.inner
        label(content, "EDIT TASK" if task else "NEW TASK", font=(FONT_FAMILY, 24, "bold"),
              text_color=COLORS["text"]).pack(anchor="w", pady=(0, 16))
        label(content,
              "AuraPlan predicts mental load from the task details; you can change its suggestion below.",
              font=(FONT_FAMILY, 11), text_color=COLORS["muted"], wraplength=470,
              justify="left").pack(anchor="w", pady=(0, 8))

        self.title_var = tk.StringVar(value=task.title if task else initial_title)
        try:
            existing_deadline = datetime.fromisoformat(task.deadline) if task and task.deadline else None
        except ValueError:
            existing_deadline = None
        self.deadline_timezone = existing_deadline.tzinfo if existing_deadline else None
        self.date_var = tk.StringVar(value=existing_deadline.date().isoformat() if existing_deadline else "")
        self.hour_var = tk.StringVar(value=existing_deadline.strftime("%I") if existing_deadline else "06")
        self.minute_var = tk.StringVar(value=existing_deadline.strftime("%M") if existing_deadline else "00")
        self.ampm_var = tk.StringVar(value=existing_deadline.strftime("%p") if existing_deadline else "PM")
        self.minutes_var = tk.StringVar(value=str(task.estimated_minutes if task else 45))
        self._field(content, "Task title", self.title_var, "e.g. Biology chapter review")
        deadline_header = frame(content, fg_color="transparent")
        deadline_header.pack(fill="x", pady=(10, 6))
        label(deadline_header, "Deadline", font=(FONT_FAMILY, 13, "bold")).pack(side="left")
        label(deadline_header, "Pick a date, then set a time", font=(FONT_FAMILY, 10),
              text_color=COLORS["muted"]).pack(side="right")
        deadline_row = frame(content, fg_color="transparent")
        deadline_row.pack(fill="x")
        self.date_button = button(deadline_row, self._date_button_text(), self._open_calendar,
                                  height=38, anchor="w", fg_color=COLORS["surface_alt"],
                                  hover_color=COLORS["surface"] if get_theme_mode() == "dark"
                                  else COLORS["mint"], text_color=COLORS["text"])
        self.date_button.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.time_button = button(deadline_row, self._clock_text(), self._open_clock_picker,
                                  width=142, height=38, fg_color=COLORS["surface_alt"],
                                  hover_color=COLORS["surface"] if get_theme_mode() == "dark"
                                  else COLORS["mint"], text_color=COLORS["text"])
        self.time_button.pack(side="left")
        self._field(content, "Estimated minutes", self.minutes_var, "45")
        label(content, "Description", font=(FONT_FAMILY, 13, "bold")).pack(anchor="w", pady=(10, 5))
        self.description = textbox(content, height=120 if CUSTOM else 7, wrap="word")
        self.description.pack(fill="x")
        if task and task.description:
            self.description.insert("1.0", task.description)

        self.load_choice = tk.StringVar(value="Automatic")
        load_panel = frame(content, fg_color=COLORS["surface_alt"])
        load_panel.pack(fill="x", pady=(12, 0))
        load_header = frame(load_panel, fg_color="transparent")
        load_header.pack(fill="x", padx=12, pady=(10, 7))
        label(load_header, "Mental load", font=(FONT_FAMILY, 14, "bold")).pack(anchor="w")
        label(load_header, "Suggested from task details · change if needed",
              font=(FONT_FAMILY, 10), text_color=COLORS["muted"]).pack(anchor="w")
        self.load_menu = option_menu(
            load_panel, ["Automatic", "High", "Medium", "Low"], self.load_choice,
            command=self._update_load_prediction, height=38,
        )
        self.load_menu.pack(fill="x", padx=12, pady=(0, 6))
        self.load_prediction_text = label(
            load_panel, "", font=(FONT_FAMILY, 11, "bold"),
            text_color=COLORS["leaf"] if get_theme_mode() == "dark" else COLORS["primary"],
            wraplength=440, justify="left",
        )
        self.load_prediction_text.pack(anchor="w", padx=13, pady=(0, 10))
        self.title_var.trace_add("write", self._update_load_prediction)
        self.minutes_var.trace_add("write", self._update_load_prediction)
        self.load_choice.trace_add("write", self._update_load_prediction)
        self.description.bind("<KeyRelease>", self._update_load_prediction)
        self.description.bind("<<Paste>>", self._update_load_prediction, add="+")
        self._update_load_prediction()

        self.error = label(content, "", text_color=COLORS["danger"])
        self.error.pack(anchor="w", pady=(10, 0))
        button(content, "Save task", self._save, height=40).pack(fill="x", pady=(14, 0))

    def _date_button_text(self):
        value = self.date_var.get()
        if not value:
            return "Choose deadline date  ▾"
        try:
            return datetime.strptime(value, "%Y-%m-%d").strftime("📅  %A, %b %d, %Y  ▾")
        except ValueError:
            return "Choose deadline date  ▾"

    def _clock_text(self):
        return f"◷  {self.hour_var.get()}:{self.minute_var.get()} {self.ampm_var.get()}"

    def _open_clock_picker(self):
        if self.clock_window is not None:
            try:
                if self.clock_window.winfo_exists():
                    self.clock_window.lift()
                    return
            except tk.TclError:
                pass
        self.clock_window = ctk.CTkToplevel(self.window) if CUSTOM else tk.Toplevel(self.window)
        self.clock_window.title("Choose time")
        self.clock_window.geometry("380x300")
        self.clock_window.resizable(False, False)
        if CUSTOM:
            self.clock_window.configure(fg_color=COLORS["background"])
        else:
            self.clock_window.configure(bg=COLORS["background"])
        self.clock_window.transient(self.window)
        self.clock_window.grab_set()
        self.clock_window.protocol("WM_DELETE_WINDOW", self._close_clock)

        self.clock_hour = tk.StringVar(value=self.hour_var.get())
        self.clock_minute = tk.StringVar(value=self.minute_var.get())
        self.clock_ampm = tk.StringVar(value=self.ampm_var.get())
        panel = frame(self.clock_window, fg_color=COLORS["surface"])
        panel.pack(fill="both", expand=True, padx=14, pady=14)
        label(panel, "SET DEADLINE TIME", font=(FONT_FAMILY, 11, "bold"),
              text_color=COLORS["muted"]).pack(pady=(15, 3))
        self.clock_preview = label(panel, "", font=(FONT_FAMILY, 30, "bold"),
                                   text_color=COLORS["text"])
        self.clock_preview.pack(pady=(0, 16))
        self._update_clock_preview()

        controls = frame(panel, fg_color="transparent")
        controls.pack(fill="x", padx=8)
        choices = (("HOUR", [f"{value:02d}" for value in range(1, 13)], self.clock_hour),
                   ("MINUTE", [f"{value:02d}" for value in range(60)], self.clock_minute))
        for column, (caption, values, variable) in enumerate(choices):
            section = frame(controls, fg_color="transparent")
            section.grid(row=0, column=column, padx=7, sticky="ew")
            label(section, caption, font=(FONT_FAMILY, 10, "bold"),
                  text_color=COLORS["muted"]).pack(pady=(0, 5))
            menu = option_menu(section, values, variable, command=lambda _value: self._update_clock_preview(),
                               width=84 if CUSTOM else 6, height=36)
            menu.pack(fill="x")
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=1)
        period = frame(controls, fg_color="transparent")
        period.grid(row=0, column=2, padx=7, sticky="ew")
        label(period, "AM / PM", font=(FONT_FAMILY, 10, "bold"),
              text_color=COLORS["muted"]).pack(pady=(0, 5))
        if CUSTOM:
            ctk.CTkSegmentedButton(
                period, values=["AM", "PM"], variable=self.clock_ampm, corner_radius=12,
                selected_color=COLORS["primary"],
                selected_hover_color=COLORS["primary"] if get_theme_mode() == "dark"
                else COLORS["leaf"],
                unselected_color=COLORS["surface_alt"],
                unselected_hover_color=COLORS["surface"] if get_theme_mode() == "dark"
                else COLORS["mint"],
                text_color=COLORS["mint"] if get_theme_mode() == "dark" else COLORS["forest"],
                command=lambda _value: self._update_clock_preview(),
            ).pack(fill="x")
        else:
            from tkinter import ttk
            ttk.Combobox(period, values=["AM", "PM"], textvariable=self.clock_ampm,
                         state="readonly", width=5).pack(fill="x")
            self.clock_ampm.trace_add("write", lambda *_args: self._update_clock_preview())
        self.clock_hour.trace_add("write", lambda *_args: self._update_clock_preview())
        self.clock_minute.trace_add("write", lambda *_args: self._update_clock_preview())
        actions = frame(panel, fg_color="transparent")
        actions.pack(fill="x", padx=8, pady=(16, 10))
        button(actions, "Cancel", self._schedule_close_clock, width=90, height=36,
               fg_color=COLORS["surface_alt"],
               hover_color=COLORS["surface"] if get_theme_mode() == "dark" else COLORS["mint"],
               text_color=COLORS["text"]).pack(side="right", padx=(8, 0))
        button(actions, "Use this time", self._apply_clock_time,
               width=130, height=36).pack(side="right")

    def _update_clock_preview(self):
        if getattr(self, "clock_preview", None) is not None:
            try:
                if self.clock_preview.winfo_exists():
                    self.clock_preview.configure(
                        text=f"{self.clock_hour.get()}:{self.clock_minute.get()} {self.clock_ampm.get()}")
            except tk.TclError:
                pass

    def _apply_clock_time(self):
        self.hour_var.set(self.clock_hour.get())
        self.minute_var.set(self.clock_minute.get())
        self.ampm_var.set(self.clock_ampm.get())
        self.time_button.configure(text=self._clock_text())
        self._schedule_close_clock()

    def _schedule_close_clock(self):
        clock_window = self.clock_window
        if clock_window is not None:
            try:
                if clock_window.winfo_exists():
                    clock_window.after(250, self._close_clock)
                    return
            except tk.TclError:
                pass
        self._close_clock()

    def _close_clock(self):
        clock_window = self.clock_window
        if clock_window is not None:
            try:
                if clock_window.winfo_exists():
                    clock_window.grab_release()
                    clock_window.destroy()
            except tk.TclError:
                pass
        self.clock_window = None
        try:
            self.window.grab_set()
        except tk.TclError:
            pass

    def _open_calendar(self):
        if getattr(self, "calendar_window", None) is not None:
            try:
                if self.calendar_window.winfo_exists():
                    self.calendar_window.lift()
                    return
            except tk.TclError:
                pass
        try:
            selected = date.fromisoformat(self.date_var.get())
        except ValueError:
            selected = date.today()
        self.calendar_month = selected.replace(day=1)
        self.calendar_window = ctk.CTkToplevel(self.window) if CUSTOM else tk.Toplevel(self.window)
        self.calendar_window.title("Choose deadline")
        self.calendar_window.geometry("380x430")
        self.calendar_window.resizable(False, False)
        if CUSTOM:
            self.calendar_window.configure(fg_color=COLORS["background"])
        else:
            self.calendar_window.configure(bg=COLORS["background"])
        self.calendar_window.transient(self.window)
        self.calendar_window.grab_set()
        self.calendar_window.protocol("WM_DELETE_WINDOW", self._close_calendar)
        panel = frame(self.calendar_window, fg_color=COLORS["surface"])
        panel.pack(fill="both", expand=True, padx=14, pady=14)
        month_row = frame(panel, fg_color="transparent")
        month_row.pack(fill="x", padx=8, pady=(8, 12))
        button(month_row, "‹", lambda: self._change_calendar_month(-1), width=42,
               height=36).pack(side="left")
        self.calendar_title = label(month_row, "", font=(FONT_FAMILY, 16, "bold"))
        self.calendar_title.pack(side="left", fill="x", expand=True)
        button(month_row, "›", lambda: self._change_calendar_month(1), width=42,
               height=36).pack(side="right")
        weekdays = frame(panel, fg_color="transparent")
        weekdays.pack(fill="x", padx=8)
        for index, name in enumerate(("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")):
            label(weekdays, name, font=(FONT_FAMILY, 10, "bold"),
                  text_color=COLORS["muted"], width=40).grid(row=0, column=index, padx=1, pady=3)
        self.calendar_grid = frame(panel, fg_color="transparent")
        self.calendar_grid.pack(fill="x", padx=8)
        self._render_calendar()
        button(panel, "Today", self._select_today, width=88, height=34,
               fg_color=COLORS["surface_alt"],
               hover_color=COLORS["surface"] if get_theme_mode() == "dark" else COLORS["mint"],
               text_color=COLORS["text"]).pack(anchor="e", padx=10, pady=(10, 8))

    def _change_calendar_month(self, offset):
        month_index = self.calendar_month.month - 1 + offset
        year = self.calendar_month.year + month_index // 12
        month = month_index % 12 + 1
        self.calendar_month = date(year, month, 1)
        if self._calendar_render_after is not None:
            try:
                self.calendar_window.after_cancel(self._calendar_render_after)
            except tk.TclError:
                pass
        self._calendar_render_after = self.calendar_window.after(
            250, self._render_calendar_after_click
        )

    def _render_calendar_after_click(self):
        self._calendar_render_after = None
        if self.calendar_window is not None:
            try:
                if self.calendar_window.winfo_exists():
                    self._render_calendar()
            except tk.TclError:
                pass

    def _render_calendar(self):
        for child in self.calendar_grid.winfo_children():
            child.destroy()
        self.calendar_title.configure(text=self.calendar_month.strftime("%B %Y"))
        selected = self.date_var.get()
        selected_date = date.fromisoformat(selected) if selected else None
        for week_index, week in enumerate(calendar.monthcalendar(
                self.calendar_month.year, self.calendar_month.month)):
            for day_index, day_number in enumerate(week):
                if not day_number:
                    label(self.calendar_grid, "", width=40, height=36).grid(
                        row=week_index, column=day_index, padx=1, pady=1)
                    continue
                current = date(self.calendar_month.year, self.calendar_month.month, day_number)
                chosen = current == selected_date
                today = current == date.today()
                dark_mode = get_theme_mode() == "dark"
                button(self.calendar_grid, str(day_number),
                       lambda selected_day=current: self._select_date(selected_day),
                       width=40, height=36,
                       fg_color=COLORS["primary"] if chosen else
                           (COLORS["leaf"] if dark_mode else COLORS["mint"]) if today
                           else COLORS["surface_alt"],
                       hover_color=(COLORS["leaf"] if dark_mode and today else
                                    COLORS["primary"] if dark_mode else COLORS["mint"]),
                       text_color="#FFFFFF" if chosen else
                           COLORS["forest"] if today or not dark_mode else COLORS["text"]).grid(
                           row=week_index, column=day_index, padx=1, pady=1)

    def _select_today(self):
        self._select_date(date.today())

    def _select_date(self, selected):
        self.date_var.set(selected.isoformat())
        self.date_button.configure(text=self._date_button_text())
        self._schedule_close_calendar()

    def _schedule_close_calendar(self):
        calendar_window = self.calendar_window
        if calendar_window is not None:
            try:
                if calendar_window.winfo_exists():
                    calendar_window.after(250, self._close_calendar)
                    return
            except tk.TclError:
                pass
        self._close_calendar()

    def _close_calendar(self):
        calendar_window = getattr(self, "calendar_window", None)
        if self._calendar_render_after is not None and calendar_window is not None:
            try:
                calendar_window.after_cancel(self._calendar_render_after)
            except tk.TclError:
                pass
            self._calendar_render_after = None
        if calendar_window is not None:
            try:
                if calendar_window.winfo_exists():
                    calendar_window.grab_release()
                    calendar_window.destroy()
            except tk.TclError:
                pass
        self.calendar_window = None
        try:
            self.window.grab_set()
        except tk.TclError:
            pass

    def _field(self, parent, title, variable, placeholder):
        label(parent, title, font=(FONT_FAMILY, 13, "bold")).pack(anchor="w", pady=(10, 6))
        entry(parent, variable=variable, placeholder=placeholder, height=36).pack(fill="x")

    def _update_load_prediction(self, *_args):
        description = self.description.get("1.0", "end-1c") if hasattr(self, "description") else ""
        try:
            duration = int(self.minutes_var.get())
        except (TypeError, ValueError):
            duration = None
        self.load_prediction = classify_task_detail(
            self.title_var.get(), description, estimated_minutes=duration, default="medium"
        )
        predicted = self.load_prediction["level"].title()
        reason = self.load_prediction["reason"]
        choice = self.load_choice.get()
        if choice == "Automatic":
            text = f"Suggested: {predicted} load · {reason}"
        else:
            text = f"Suggested: {predicted} load · {reason}\nUsing your choice: {choice} load"
        self.load_prediction_text.configure(text=text)

    def _save(self):
        title = self.title_var.get().strip()
        if not title:
            self.error.configure(text="Please enter a task title.")
            return
        deadline_input = self.date_var.get().strip()
        try:
            hour_12 = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            if not 1 <= hour_12 <= 12 or not 0 <= minute <= 59:
                raise ValueError
            hour_24 = hour_12 % 12 + (12 if self.ampm_var.get() == "PM" else 0)
            deadline = datetime.strptime(
                f"{deadline_input} {hour_24:02d}:{minute:02d}", "%Y-%m-%d %H:%M"
            ).replace(tzinfo=self.deadline_timezone).isoformat()
        except ValueError:
            self.error.configure(text="Choose a date and a valid time using the clock picker.")
            return
        try:
            minutes = int(self.minutes_var.get())
            if minutes <= 0:
                raise ValueError
        except ValueError:
            self.error.configure(text="Estimated minutes must be a positive whole number.")
            return
        description = self.description.get("1.0", "end-1c").strip()
        self._update_load_prediction()
        load_level = (self.load_prediction["level"] if self.load_choice.get() == "Automatic"
                      else self.load_choice.get().casefold())
        values = dict(title=title, deadline=deadline, estimated_minutes=minutes,
                      description=description, load_level=load_level)
        try:
            self.on_save(values, self.task)
        except Exception as exc:
            self.error.configure(text=f"Could not save task: {exc}")
            return
        # CustomTkinter schedules focus/hover callbacks for the clicked button.
        # Let them run before destroying the form and its child widgets.
        try:
            self.window.after(250, self.window.destroy)
        except tk.TclError:
            pass

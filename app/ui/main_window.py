"""AuraPlan desktop app with an animated, non-blocking startup screen."""
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from time import monotonic
import ctypes
import sys

from dashboard import Dashboard
from profile_store import ProfileStore
from task_repository import TaskRepository
from ui_compat import (COLORS, CUSTOM, ctk, button, energy_selector, frame, label,
                       brand_mark_image, get_theme_mode, messagebox, progress, root, set_progress,
                       scrollable, set_theme, tk, typeface)


class AuraPlanApp:
    def __init__(self):
        self._set_windows_app_id()
        self.window = root()
        self.window.title("AuraPlan · Study with intention")
        self.icons_dir = self._icons_directory()
        self.theme_icon = self._load_theme_icon()
        self._set_window_icon()
        if sys.platform == "win32":
            # Apply after Tk has mapped the root HWND; on Windows 11 the
            # taskbar may ignore an icon set only before the first map event.
            self.window.after(100, self._apply_windows_taskbar_icon)
        self.window.geometry("1280x850")
        self.window.minsize(980, 680)
        self._startup_started = monotonic()
        self._startup_result = Queue()
        self._profile_result = Queue()
        self.profile_store = None
        self.profiles = []
        self.profile = None
        self._voice_result = Queue()
        self.voice_error = None
        self.voice_input = None
        self.voice_loading = False
        self._voice_model_loading = False
        self._startup_value = 0.0
        self._startup_target = 0.0
        self._startup_phase = "Preparing AuraPlan…"
        self._startup_done = False
        self._build_startup_screen()
        self.window.update_idletasks()
        Thread(target=self._load_profiles, name="AuraPlanProfiles", daemon=True).start()
        self.window.after(60, self._poll_profiles)

    def _build_startup_screen(self):
        self.startup_panel = frame(self.window, fg_color=COLORS["forest"], corner_radius=0)
        self.startup_panel.pack(fill="both", expand=True)
        card = frame(self.startup_panel, width=480, height=350, fg_color=COLORS["surface"],
                     corner_radius=30)
        card.pack(expand=True)
        card.pack_propagate(False)
        self.startup_brand = brand_mark_image(card, 72)
        if self.startup_brand is not None:
            label(card, image=self.startup_brand, text="", width=72, height=72).pack(
                pady=(26, 0))
        else:
            label(card, "✦", font=typeface(24, "bold"),
                  text_color=COLORS["leaf"]).pack(pady=(26, 0))
        label(card, "AURAPLAN", font=typeface(30, "bold"),
              text_color=COLORS["text"]).pack(pady=(2, 5))
        label(card, "Your calm academic planner", font=typeface(15),
              text_color=COLORS["muted"]).pack(pady=(0, 27))
        self.startup_status = label(card, "Getting your workspace ready…",
                                    font=typeface(12), text_color=COLORS["muted"])
        self.startup_status.pack(pady=(0, 14))
        self.startup_progress = progress(card, width=300, height=12)
        self.startup_progress.pack(pady=(0, 32))
        set_progress(self.startup_progress, 0)

    def _load_profiles(self):
        try:
            self._profile_result.put((ProfileStore(), None))
        except Exception as exc:
            self._profile_result.put((None, exc))

    def _poll_profiles(self):
        try:
            self.profile_store, error = self._profile_result.get_nowait()
        except Empty:
            if (monotonic() - self._startup_started) * 1000 < 1000:
                self.window.after(60, self._poll_profiles)
            else:
                self.startup_status.configure(text="Preparing your profiles…")
                self.window.after(60, self._poll_profiles)
            return
        if error:
            self.startup_panel.destroy()
            messagebox.showerror("AuraPlan startup", f"Could not load profiles.\n\n{error}",
                                 parent=self.window)
            self.window.destroy()
            return
        self.profiles = self.profile_store.list_profiles()
        elapsed = (monotonic() - self._startup_started) * 1000
        if elapsed < 1000:
            self.window.after(int(1000 - elapsed), self._show_profile_picker)
        else:
            self._show_profile_picker()

    def _show_profile_picker(self):
        if hasattr(self, "startup_panel") and self.startup_panel.winfo_exists():
            self.startup_panel.destroy()
        self.profile_panel = frame(self.window, fg_color=COLORS["background"], corner_radius=0)
        self.profile_panel.pack(fill="both", expand=True)
        card = frame(self.profile_panel, width=700, fg_color=COLORS["surface"])
        card.pack(expand=True, padx=24, pady=28)
        card.pack_propagate(False)
        card.configure(height=620)
        self.profile_brand = brand_mark_image(card, 58)
        if self.profile_brand is not None:
            label(card, image=self.profile_brand, text="", width=58, height=58).pack(pady=(30, 10))
        label(card, "Who's planning today?", font=typeface(28, "bold")).pack(pady=(0, 5))
        label(card, "Choose a local profile to open its private study workspace.",
              font=typeface(13), text_color=COLORS["muted"]).pack(pady=(0, 22))
        profile_scroller = scrollable(card, height=300)
        profile_scroller.pack(fill="both", expand=True, padx=36)
        profiles_area = profile_scroller if CUSTOM else profile_scroller.inner
        for index, profile in enumerate(self.profiles):
            letter = profile["name"].strip()[:1].upper()
            row = frame(profiles_area, fg_color=COLORS["surface_alt"])
            row.pack(fill="x", pady=5)
            avatar = frame(row, width=48, height=48, fg_color=COLORS["primary"],
                           corner_radius=24)
            avatar.pack_propagate(False)
            label(avatar, letter, font=typeface(20, "bold"),
                  text_color=COLORS["mint"]).pack(expand=True)
            avatar.pack(side="left", padx=12, pady=10)
            info = frame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=(0, 8))
            label(info, profile["name"], font=typeface(15, "bold")).pack(anchor="w")
            label(info, "Local profile · stored on this device", font=typeface(11),
                  text_color=COLORS["muted"]).pack(anchor="w")
            button(row, "Open", lambda item=profile: self._select_profile(item),
                   width=92, height=38).pack(side="right", padx=12, pady=10)

        create_row = frame(card, fg_color="transparent")
        create_row.pack(fill="x", padx=36, pady=(16, 30))
        self.new_profile_name = tk.StringVar()
        self.new_profile_name_entry = entry(
            create_row, variable=self.new_profile_name, placeholder="Add a profile name…",
            height=42)
        self.new_profile_name_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        button(create_row, "+  Add profile", self._create_profile,
               width=142, height=42).pack(side="right")
        self.new_profile_name_entry.bind("<Return>", lambda _event: self._create_profile())

    def _create_profile(self):
        try:
            profile = self.profile_store.create_profile(self.new_profile_name.get())
        except ValueError as exc:
            messagebox.showwarning("Add profile", str(exc), parent=self.window)
            return
        self.profiles = self.profile_store.list_profiles()
        self._select_profile(profile)

    def _select_profile(self, profile):
        self.profile = profile
        if hasattr(self, "profile_panel") and self.profile_panel.winfo_exists():
            self.profile_panel.destroy()
        self._startup_started = monotonic()
        self._startup_result = Queue()
        self._startup_value = 0.0
        self._startup_target = 0.0
        self._startup_phase = "Opening your profile…"
        self._startup_done = False
        self._build_startup_screen()
        self.window.update_idletasks()
        Thread(target=self._load_backend, args=(profile,),
               name="AuraPlanWorkspace", daemon=True).start()
        self.window.after(50, self._poll_startup)

    def _load_backend(self, profile):
        try:
            self._startup_result.put(("phase", 22, f"Opening {profile['name']}'s workspace…"))
            repository = TaskRepository(self.profile_store.database_path(profile["id"]))
        except Exception as exc:
            self._startup_result.put(("done", None, None, exc, None))
            return

        if self.voice_input is not None:
            self._startup_result.put(("done", repository, self._model_path, None, None))
            return
        if self.voice_error is not None:
            self._startup_result.put(("done", repository, None, None, self.voice_error))
            return
        if getattr(self, "_voice_model_loading", False):
            self._startup_result.put(("done", repository, self._model_path, None, None))
            return

        try:
            self._startup_result.put(("phase", 58, "Preparing offline voice support…"))
            import pyaudio  # Preload the microphone runtime before enabling voice input.
            import vosk  # Import Vosk's native runtime; the large model loads after the splash.
            if getattr(sys, "frozen", False):
                # Keep the large offline model beside AuraPlan.exe so the app
                # folder is portable without expanding several GB at launch.
                model_path = Path(sys.executable).resolve().parent / "model"
                bundled_model_path = Path(getattr(sys, "_MEIPASS", "")) / "model"
                if not model_path.is_dir() and bundled_model_path.is_dir():
                    model_path = bundled_model_path
            else:
                model_path = Path(__file__).resolve().parents[2] / "model"
            if not model_path.is_dir() or not any(model_path.iterdir()):
                raise FileNotFoundError(f"Vosk model folder is missing or empty: {model_path}")
            # Vosk exposes model loading as one operation. Validate its files
            # now; load the large acoustic model after the dashboard is usable.
            required_model_files = (
                model_path / "am" / "final.mdl",
                model_path / "conf" / "model.conf",
                model_path / "graph" / "HCLG.fst",
            )
            missing_files = [str(path.relative_to(model_path))
                             for path in required_model_files if not path.is_file()]
            if missing_files:
                raise ValueError(
                    f"The Vosk model is incomplete in {model_path}; missing: "
                    + ", ".join(missing_files)
                )
            self._model_path = model_path
            self._voice_model_loading = True
            Thread(target=self._load_voice_model, args=(model_path,),
                   name="AuraPlanVoskModel", daemon=True).start()
            self._startup_result.put(("done", repository, model_path, None, None))
        except Exception as exc:
            self._startup_result.put(("done", repository, None, None, exc))

    def _poll_startup(self):
        while True:
            try:
                event = self._startup_result.get_nowait()
            except Empty:
                break
            if event[0] == "phase":
                _, self._startup_target, self._startup_phase = event
            else:
                _, self._loaded_repository, self._model_path, self._startup_error, self._voice_error = event
                self._startup_done = True
                self._startup_target = 100.0
                self._startup_phase = (
                    "Opening dashboard · voice setup needs attention…"
                    if self._voice_error else "Ready — opening your dashboard…"
                )

        if not self._startup_done and "offline voice" in self._startup_phase.casefold():
            # Vosk exposes model creation as a single native call without a
            # partial-load callback. This splash phase only preloads its runtime.
            self._startup_value += max(0.08, (88.0 - self._startup_value) * 0.018)
            self._startup_value = min(88.0, self._startup_value)
        else:
            self._startup_value += max(0.1, (self._startup_target - self._startup_value) * 0.18)
            self._startup_value = min(self._startup_target, self._startup_value)
        set_progress(self.startup_progress, self._startup_value)
        self.startup_status.configure(text=self._startup_phase)

        elapsed_ms = int((monotonic() - self._startup_started) * 1000)
        if self._startup_done and elapsed_ms >= 1500:
            self._startup_value = 100.0
            set_progress(self.startup_progress, self._startup_value)
            self.window.after(100, self._finish_startup)
            return
        self.window.after(50, self._poll_startup)

    def _finish_startup(self):
        self.startup_panel.destroy()
        if self._startup_error:
            messagebox.showerror(
                "AuraPlan startup",
                f"Could not load the local task database.\n\n{self._startup_error}",
                parent=self.window,
            )
            self.window.destroy()
            return
        self.repo = self._loaded_repository
        self.voice_error = self._voice_error
        self.voice_loading = not bool(self.voice_error or self.voice_input)
        self._build_shell()
        if self.voice_input:
            self.dashboard.set_voice_ready(self.voice_input)
        elif self._voice_error:
            self.dashboard.set_voice_unavailable(self._voice_error)
        else:
            self.dashboard.set_voice_loading()

    def _load_voice_model(self, model_path):
        try:
            from app.voices.voice_input import VoiceInput
            self._voice_result.put((VoiceInput(model_path=model_path), None))
        except Exception as exc:
            self._voice_result.put((None, exc))

    def _poll_voice_model(self):
        self._voice_poll_after = None
        try:
            voice_input, error = self._voice_result.get_nowait()
        except Empty:
            self._voice_poll_after = self.window.after(120, self._poll_voice_model)
            return
        self._voice_model_loading = False
        self.voice_input = voice_input
        self.voice_error = error
        self.voice_loading = False
        if hasattr(self, "dashboard"):
            try:
                if self.dashboard.panel.winfo_exists():
                    if error:
                        self.dashboard.set_voice_unavailable(error)
                    else:
                        self.dashboard.set_voice_ready(voice_input)
            except tk.TclError:
                pass

    def _build_shell(self, state=None):
        shell = frame(self.window, fg_color=COLORS["background"])
        self.shell = shell
        shell.pack(fill="both", expand=True)
        self.sidebar = frame(shell, width=230, fg_color=COLORS["forest"], corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        brand = frame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=18, pady=(26, 34))
        self.brand_mark = brand_mark_image(brand, 44)
        if self.brand_mark is not None:
            label(brand, image=self.brand_mark, text="", width=44, height=44).pack(side="left", padx=(0, 10))
        label(brand, "AURAPLAN", font=typeface(19, "bold"), text_color=COLORS["mint"]).pack(side="left")
        label(self.sidebar, "WORKSPACE", font=typeface(10, "bold"),
              text_color=COLORS["leaf"]).pack(anchor="w", padx=18, pady=(0, 8))
        self.nav_buttons = {}
        for view, caption in (("today", "Today"), ("tasks", "My tasks"), ("week", "7-day plan")):
            nav = button(self.sidebar, caption, lambda v=view: self.navigate(v), height=44,
                         anchor="w", fg_color="transparent", hover_color=COLORS["primary"],
                         text_color=COLORS["mint"], font=typeface(13, "bold"))
            nav.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[view] = nav
        profile_panel = frame(self.sidebar, fg_color=COLORS["primary"])
        profile_panel.pack(side="bottom", fill="x", padx=12, pady=16)
        label(profile_panel, "CURRENT PROFILE", font=typeface(9, "bold"),
              text_color=COLORS["mint"]).pack(anchor="w", padx=11, pady=(10, 1))
        label(profile_panel, self.profile["name"], font=typeface(13, "bold"),
              text_color="#FFFFFF").pack(anchor="w", padx=11, pady=(0, 7))
        button(profile_panel, "Switch profile", self._switch_profile,
               height=34, fg_color=COLORS["forest"], hover_color=COLORS["background"],
               text_color=COLORS["mint"]).pack(fill="x", padx=8, pady=(0, 8))
        self._set_active_nav(state.get("view", "today") if state else "today")
        if not hasattr(self, "energy_level"):
            self.energy_level = tk.StringVar(value="Medium")
        self.main = frame(shell, fg_color="transparent")
        self.main.pack(side="left", fill="both", expand=True)
        self.dashboard = Dashboard(self.main, self.repo, self.energy_level, None,
                                   on_toggle_theme=self._toggle_theme,
                                   theme_icon=self.theme_icon,
                                   brand_icon=self.brand_mark)
        if state:
            self.dashboard.view = state.get("view", "today")
            self.dashboard.minutes.set(state.get("minutes", "180"))
            self.dashboard.search.set(state.get("search", ""))
            self.dashboard.task_filter.set(state.get("task_filter", "All tasks"))
            self.dashboard.voice_text.set(state.get("voice_text", ""))
            self.dashboard.refresh()
        self.dashboard.show()
        if self.voice_input:
            self.dashboard.set_voice_ready(self.voice_input)
        elif self.voice_error:
            self.dashboard.set_voice_unavailable(self.voice_error)
        elif self.voice_loading:
            self.dashboard.set_voice_loading()
            if not getattr(self, "_voice_poll_after", None):
                self._voice_poll_after = self.window.after(120, self._poll_voice_model)
    def _set_active_nav(self, selected):
        for view, nav in self.nav_buttons.items():
            nav.configure(fg_color=COLORS["primary"] if view == selected else "transparent",
                          hover_color=COLORS["primary"])

    def navigate(self, view="today"):
        self.dashboard.show_view(view)
        self._set_active_nav(view)

    def _switch_profile(self):
        if getattr(self.dashboard, "voice_session", None) is not None:
            messagebox.showinfo("Voice input", "Stop voice recording before switching profiles.",
                                parent=self.window)
            return
        self.dashboard.dispose()
        self.shell.destroy()
        self._show_profile_picker()

    def _toggle_theme(self):
        if getattr(self, "_theme_change_pending", False):
            return
        if getattr(self.dashboard, "voice_session", None) is not None:
            messagebox.showinfo("Voice input", "Stop voice recording before changing the theme.",
                                parent=self.window)
            return
        state = {
            "view": self.dashboard.view,
            "minutes": self.dashboard.minutes.get(),
            "search": self.dashboard.search.get(),
            "task_filter": self.dashboard.task_filter.get(),
            "voice_text": self.dashboard.voice_text.get(),
        }
        next_mode = "dark" if get_theme_mode() == "light" else "light"
        self._theme_change_pending = True
        self.dashboard.theme_button.configure(state="disabled")
        # CTkButton schedules a focus_set callback after clicks. Let that callback
        # complete before disposing of the clicked button during the theme redraw.
        self.window.after(500, lambda: self._apply_theme(next_mode, state))

    def _apply_theme(self, mode, state):
        # Energy is a traced Tk variable shared with the selector in the shell.
        # Detach the old dashboard before destroying any of its widgets.
        self.dashboard.dispose()
        set_theme(mode, self.window)
        self.shell.destroy()
        self._build_shell(state)
        self._theme_change_pending = False

    @staticmethod
    def _icons_directory():
        bundled_root = getattr(sys, "_MEIPASS", None)
        if bundled_root:
            return Path(bundled_root) / "app" / "assets" / "icons"
        return Path(__file__).resolve().parents[1] / "assets" / "icons"

    def _load_theme_icon(self):
        icon_path = self.icons_dir / "theme-toggle.png"
        if not CUSTOM or not icon_path.is_file():
            return None
        try:
            from PIL import Image
            source = Image.open(icon_path).convert("RGBA")
            alpha = source.getchannel("A")
            bounds = alpha.getbbox()
            if bounds:
                source = source.crop(bounds)
            resampling = getattr(Image, "Resampling", Image).LANCZOS

            def tinted(color):
                glyph = source.getchannel("A")
                glyph.thumbnail((20, 20), resampling)
                image = Image.new("RGBA", (22, 22), (0, 0, 0, 0))
                image.paste(Image.new("RGBA", glyph.size, color),
                            ((22 - glyph.width) // 2, (22 - glyph.height) // 2), glyph)
                return image

            # The supplied pack uses black artwork. Tint it for contrast in
            # both themes and trim its transparent padding before shrinking.
            return ctk.CTkImage(light_image=tinted("#2E6F40"),
                                dark_image=tinted("#CFFFDC"), size=(22, 22))
        except Exception:
            return None

    def _set_window_icon(self):
        """Use app/assets/icons/auraplan.ico for the window and Windows taskbar."""
        ico_path = self.icons_dir / "auraplan.ico"
        png_path = self.icons_dir / "auraplan.png"
        if ico_path.is_file():
            try:
                self.window.iconbitmap(str(ico_path))
            except tk.TclError:
                pass
            try:
                # Tk's iconbitmap can update the title bar while Windows still
                # uses its default taskbar image. Also set a retained iconphoto.
                from PIL import Image, ImageTk
                image = Image.open(ico_path).convert("RGBA")
                image.thumbnail((128, 128), getattr(Image, "Resampling", Image).LANCZOS)
                self._window_icon_image = ImageTk.PhotoImage(image, master=self.window)
                self.window.iconphoto(True, self._window_icon_image)
            except Exception:
                self._window_icon_image = None
        if sys.platform == "win32" and ico_path.is_file():
            self._load_native_windows_icon(ico_path)
        if getattr(self, "_window_icon_image", None) is None and png_path.is_file():
            try:
                # Pillow detects the actual format, even if the file extension
                # is wrong. This is only a fallback when there is no usable ICO.
                from PIL import Image, ImageTk
                image = Image.open(png_path).convert("RGBA")
                image.thumbnail((128, 128), getattr(Image, "Resampling", Image).LANCZOS)
                self._window_icon_image = ImageTk.PhotoImage(image, master=self.window)
                self.window.iconphoto(True, self._window_icon_image)
            except Exception:
                self._window_icon_image = None

    def _load_native_windows_icon(self, ico_path):
        """Load an HICON directly so Windows receives a real taskbar icon."""
        try:
            user32 = ctypes.windll.user32
            user32.LoadImageW.restype = ctypes.c_void_p
            user32.LoadImageW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p,
                                           ctypes.c_uint, ctypes.c_int, ctypes.c_int,
                                           ctypes.c_uint]
            image_icon, load_from_file, default_size = 1, 0x0010, 0x0040
            self._native_window_icon = user32.LoadImageW(
                None, str(ico_path), image_icon, 0, 0, load_from_file | default_size
            )
        except (AttributeError, OSError, TypeError):
            self._native_window_icon = None

    def _apply_windows_taskbar_icon(self):
        """Set both window and class icons after the root HWND is available."""
        icon = getattr(self, "_native_window_icon", None)
        if sys.platform != "win32" or not icon:
            return
        try:
            user32 = ctypes.windll.user32
            user32.SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                             ctypes.c_size_t, ctypes.c_ssize_t]
            user32.SendMessageW.restype = ctypes.c_ssize_t
            user32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
            user32.GetAncestor.restype = ctypes.c_void_p
            hwnd = user32.GetAncestor(self.window.winfo_id(), 2) or self.window.winfo_id()
            wm_seticon, icon_small, icon_big = 0x0080, 0, 1
            user32.SendMessageW(hwnd, wm_seticon, icon_small, icon)
            user32.SendMessageW(hwnd, wm_seticon, icon_big, icon)
            # GCLP_HICON / GCLP_HICONSM: Windows uses these when creating the
            # taskbar thumbnail and when WM_GETICON has no specific size.
            set_class_icon = getattr(user32, "SetClassLongPtrW", None)
            if set_class_icon is not None:
                set_class_icon.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
                set_class_icon.restype = ctypes.c_void_p
                set_class_icon(hwnd, -14, icon)
                set_class_icon(hwnd, -34, icon)
        except (AttributeError, OSError, tk.TclError):
            pass

    @staticmethod
    def _set_windows_app_id():
        """Give Windows a stable taskbar identity for the AuraPlan window."""
        if sys.platform != "win32":
            return
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "AuraPlan.Desktop"
            )
        except (AttributeError, OSError):
            pass

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    AuraPlanApp().run()

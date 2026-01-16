"""
Main application class for the School Bell application.
Contains the main GUI and core functionality.
"""
import customtkinter
import threading
import time
from tkinter import *
import os
from pygame import mixer
from datetime import datetime
from config import APP_NAME, WIDTH, HEIGHT, RESOURCES_DIR, SCHEDULE_FILE
from utils import load_schedule, save_schedule, log_message
from ui_components import setup_left_panel, setup_center_panel, setup_right_panel
from audio_handler import set_volume, play_song, play_song_manual
from scheduler import start_service, stop_service, run_scheduler, update_next_bell_label
from manual_handler import manual_ring
from schedule_editor import ScheduleEditorWindow
from about_dialog import AboutDialog


class SchoolBellApp(customtkinter.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(APP_NAME)
        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.resizable(True, True)
        customtkinter.set_appearance_mode("dark")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.editor_window = None
        self.songs_window = None
        self.last_csv_mod_time = 0
        self.quiet_mode = customtkinter.BooleanVar()
        self.manual_ring_playing_thread = None # New attribute to track manual play thread

        if not os.path.exists(RESOURCES_DIR):
            os.makedirs(RESOURCES_DIR)

        # Initialize song list
        self.song_list = ["Случайна"] + [s for s in os.listdir(RESOURCES_DIR) if s.endswith((".mp3", ".wav", ".ogg"))]

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure(2, weight=3)
        self.grid_rowconfigure(0, weight=1)

        self.setup_left_panel()
        self.setup_center_panel()
        self.setup_right_panel()

        self.service_running = False
        self.scheduler_thread = None
        mixer.init()
        mixer.music.set_volume(0.5) # Set default volume

        self.bell_times = load_schedule()
        log_message(self, "Приложението е готово. Натиснете 'СТАРТ'.")

        self.start_ui_update_loops()

    def start_ui_update_loops(self):
        # Update digital clock
        self.update_digital_clock()
        # Update schedule display
        self.populate_schedule_display()
        # Update next bell label
        self.update_next_bell_label()

        # Check for external CSV changes
        try:
            mod_time = os.path.getmtime(SCHEDULE_FILE)
            if self.last_csv_mod_time != 0 and mod_time != self.last_csv_mod_time:
                log_message(self, "Открита е промяна в schedule.csv. Презареждане...")
                self.reload_schedule_from_csv()
            self.last_csv_mod_time = mod_time
        except FileNotFoundError:
            pass # Handled by load_schedule

        # Schedule next update
        self.after(1000, self.start_ui_update_loops)

    def reload_schedule_from_csv(self):
        self.bell_times = load_schedule()
        log_message(self, "Програмата е презаредена от CSV файла.")
        if self.service_running:
            log_message(self, "Рестартиране на услугата с новата програма...")
            self.stop_service()
            self.start_service()

    def setup_left_panel(self):
        setup_left_panel(self)

    def setup_center_panel(self):
        setup_center_panel(self)

    def setup_right_panel(self):
        setup_right_panel(self)

    def set_volume(self, volume):
        set_volume(volume)
        # Update the volume percentage label
        volume_percent = int(float(volume) * 100)
        self.volume_percentage_label.configure(text=f"{volume_percent}%")

    def manual_ring(self):
        manual_ring(self)

    def _play_manual_bell(self, song_name=None):
        play_song_manual(self, song_name=song_name)
        # Only reset button if music wasn't stopped externally
        if self.manual_ring_button.cget("text") == "Спри звънеца":
            self.after(0, self._reset_manual_ring_button)

    def _reset_manual_ring_button(self):
        self.manual_ring_button.configure(text="Пусни звънеца сега", fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])
        self.manual_ring_playing_thread = None
        log_message(self, "Ръчен звънец приключи.")

    def update_digital_clock(self):
        self.digital_clock_label.configure(text=datetime.now().strftime("%H:%M:%S"))

    def populate_schedule_display(self):
        for widget in self.schedule_display_frame.winfo_children():
            widget.destroy()
        from config import BG_WEEKDAYS
        today_weekday_bg = BG_WEEKDAYS[datetime.now().weekday()]
        self.schedule_display_title.configure(text=f"Програма за {today_weekday_bg}:")
        todays_bells = sorted([entry for entry in self.bell_times if entry['day'] == today_weekday_bg], key=lambda x: x['time'])
        if not todays_bells:
            customtkinter.CTkLabel(self.schedule_display_frame, text="Няма звънци за днес.").pack(pady=10, padx=10)
        else:
            for entry in todays_bells:
                song_display = entry.get('song') if entry.get('song') else "Случайна"
                customtkinter.CTkLabel(self.schedule_display_frame, text=f"{entry['time']} ({song_display})", font=customtkinter.CTkFont(size=14)).pack(pady=5, padx=10, anchor="w")

    def open_schedule_editor(self):
        if self.editor_window is None or not self.editor_window.winfo_exists():
            self.editor_window = ScheduleEditorWindow(self)
            self.editor_window.grab_set()
        else:
            self.editor_window.focus()

    def show_about(self):
        AboutDialog(self)

    def update_schedule(self, new_schedule):
        self.bell_times = new_schedule
        save_schedule(new_schedule)
        log_message(self, "Програмата беше обновена.")
        if self.service_running:
            log_message(self, "Рестартиране на услугата с новата програма...")
            self.stop_service()
            self.start_service()

    def log_message(self, msg):
        log_message(self, msg)

    def toggle_service(self):
        if self.service_running:
            self.stop_service()
        else:
            self.start_service()

    def start_service(self):
        start_service(self)

    def stop_service(self):
        stop_service(self)

    def run_scheduler(self):
        run_scheduler(self)

    def update_next_bell_label(self):
        update_next_bell_label(self)

    def play_song(self, song_name=None):
        return play_song(self, song_name)

    def on_closing(self):
        if self.service_running:
            self.stop_service()
        if self.editor_window:
            self.editor_window.destroy()
        if self.songs_window:
            self.songs_window.destroy()
        self.destroy()
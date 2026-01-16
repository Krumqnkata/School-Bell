import customtkinter
import threading
import schedule
import time
from tkinter import *
import random
import os
from pygame import mixer
from datetime import datetime, timedelta
import csv

# --- App Conf ---
APP_NAME = "Училищен Звънец v2.4"
WIDTH = 1100
HEIGHT = 700
RESOURCES_DIR = "songs"
SCHEDULE_FILE = "schedule.csv"

# --- Colors ---
GREEN = "#2CC985"
RED = "#E84545"
BLUE = "#3a7ebf"

# --- Day Mapping ---
DAY_MAP_BG_TO_EN = {
    "Понеделник": "monday", "Вторник": "tuesday", "Сряда": "wednesday",
    "Четвъртък": "thursday", "Петък": "friday", "Събота": "saturday", "Неделя": "sunday",
}
DAYS_OF_WEEK = list(DAY_MAP_BG_TO_EN.keys())
BG_WEEKDAYS = ["Понеделник", "Вторник", "Сряда", "Четвъртък", "Петък", "Събота", "Неделя"]

class ScheduleEditorWindow(customtkinter.CTkToplevel):
    def __init__(self, parent_app):
        super().__init__(parent_app)
        self.parent_app = parent_app
        self.title("Редактор на програмата")
        self.geometry("700x750")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.transient(parent_app)

        self.temp_schedule = [dict(entry) for entry in self.parent_app.bell_times]
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.editor_frame = customtkinter.CTkScrollableFrame(self, label_text="Пълна програма")
        self.editor_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        self.populate_editor()

        add_frame = customtkinter.CTkFrame(self)
        add_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=5)
        add_frame.columnconfigure(1, weight=1)

        self.day_var = customtkinter.StringVar(value=DAYS_OF_WEEK[0])
        customtkinter.CTkOptionMenu(add_frame, variable=self.day_var, values=DAYS_OF_WEEK, width=120).grid(row=0, column=0, padx=(0,5))
        self.time_entry = customtkinter.CTkEntry(add_frame, placeholder_text="ЧЧ:ММ")
        self.time_entry.grid(row=0, column=1, sticky="ew")

        self.song_list = ["Случайна"] + [s for s in os.listdir(RESOURCES_DIR) if s.endswith((".mp3", ".wav", ".ogg"))]
        self.song_var = customtkinter.StringVar(value=self.song_list[0])
        customtkinter.CTkOptionMenu(add_frame, variable=self.song_var, values=self.song_list, width=140).grid(row=0, column=2, padx=5)

        customtkinter.CTkButton(add_frame, text="+", width=30, command=self.add_schedule_entry).grid(row=0, column=3, padx=(5,0))

        self.setup_bulk_edit_frame()

        customtkinter.CTkButton(self, text="Запази и затвори", command=self.save_and_close).grid(row=4, column=0, padx=20, pady=(10,5), sticky="ew")
        customtkinter.CTkButton(self, text="Отказ", fg_color="gray", command=self.cancel).grid(row=5, column=0, padx=20, pady=5, sticky="ew")

    def setup_bulk_edit_frame(self):
        bulk_edit_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        bulk_edit_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        bulk_edit_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(bulk_edit_frame, text="Масово редактиране:", font=customtkinter.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 5))

        customtkinter.CTkLabel(bulk_edit_frame, text="Копирай от:").grid(row=1, column=0, sticky="w", padx=5)
        self.bulk_source_day_var = customtkinter.StringVar(value=DAYS_OF_WEEK[0])
        customtkinter.CTkOptionMenu(bulk_edit_frame, variable=self.bulk_source_day_var, values=DAYS_OF_WEEK, width=120).grid(row=1, column=1, sticky="w")

        customtkinter.CTkLabel(bulk_edit_frame, text="Копирай в:").grid(row=2, column=0, sticky="w", padx=5, pady=(5,0))
        
        self.bulk_target_day_vars = {}
        targets_frame = customtkinter.CTkFrame(bulk_edit_frame, fg_color="transparent")
        targets_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=5)
        for i, day in enumerate(DAYS_OF_WEEK):
            var = customtkinter.StringVar()
            cb = customtkinter.CTkCheckBox(targets_frame, text=day, variable=var, onvalue=day, offvalue="")
            cb.grid(row=i // 4, column=i % 4, padx=5, pady=2, sticky="w")
            self.bulk_target_day_vars[day] = var

        customtkinter.CTkButton(bulk_edit_frame, text="Копирай", command=self.bulk_copy_schedule).grid(row=4, column=0, columnspan=3, sticky="ew", pady=(10,0))


    def bulk_copy_schedule(self):
        source_day = self.bulk_source_day_var.get()
        target_days = [var.get() for var in self.bulk_target_day_vars.values() if var.get()]

        if not target_days:
            return

        source_schedule = [entry for entry in self.temp_schedule if entry['day'] == source_day]
        
        # Remove existing entries for target days
        self.temp_schedule = [entry for entry in self.temp_schedule if entry['day'] not in target_days]
        
        # Add new entries
        for day in target_days:
            for source_entry in source_schedule:
                new_entry = source_entry.copy()
                new_entry['day'] = day
                self.temp_schedule.append(new_entry)
        
        self.populate_editor()

    def populate_editor(self):
        for widget in self.editor_frame.winfo_children():
            widget.destroy()
        self.temp_schedule.sort(key=lambda x: (DAYS_OF_WEEK.index(x['day']), x['time']))
        self.entry_widgets = {} 
        for entry in self.temp_schedule:
            entry_id = id(entry)
            frame = customtkinter.CTkFrame(self.editor_frame)
            frame.pack(fill="x", padx=5, pady=5)
            frame.columnconfigure(1, weight=1)
            
            song_display = entry.get('song') if entry.get('song') else "Случайна"
            label = customtkinter.CTkLabel(frame, text=f"{entry['day']} - {entry['time']} ({song_display})")
            label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            
            edit_button = customtkinter.CTkButton(frame, text="Промени", width=70, fg_color=BLUE, command=lambda e=entry, f=frame: self.toggle_inline_edit(e, f))
            edit_button.grid(row=0, column=2, padx=5)
            delete_button = customtkinter.CTkButton(frame, text="Изтрий", width=60, fg_color=RED, command=lambda e=entry, f=frame: self.delete_schedule_entry(e, f))
            delete_button.grid(row=0, column=3, padx=5)
            self.entry_widgets[entry_id] = {'frame': frame, 'label': label, 'edit_button': edit_button}

    def toggle_inline_edit(self, entry, frame):
        widgets = self.entry_widgets[id(entry)]
        widgets['label'].grid_forget()
        widgets['edit_button'].configure(text="Запази", fg_color=GREEN, command=lambda e=entry, f=frame: self.save_inline_edit(e, f))
        
        inline_day_var = customtkinter.StringVar(value=entry['day'])
        inline_day_menu = customtkinter.CTkOptionMenu(frame, variable=inline_day_var, values=DAYS_OF_WEEK, width=120)
        inline_day_menu.grid(row=0, column=0, sticky="w", padx=5)
        
        inline_time_entry = customtkinter.CTkEntry(frame, width=60)
        inline_time_entry.insert(0, entry['time'])
        inline_time_entry.grid(row=0, column=1, sticky="w", padx=5)

        current_song = entry.get('song') if entry.get('song') else "Случайна"
        inline_song_var = customtkinter.StringVar(value=current_song)
        inline_song_menu = customtkinter.CTkOptionMenu(frame, variable=inline_song_var, values=self.song_list, width=140)
        inline_song_menu.grid(row=0, column=1, sticky="w", padx=(70,5))
        
        widgets['inline_day_var'] = inline_day_var
        widgets['inline_day_menu'] = inline_day_menu
        widgets['inline_time_entry'] = inline_time_entry
        widgets['inline_song_var'] = inline_song_var
        widgets['inline_song_menu'] = inline_song_menu


    def save_inline_edit(self, entry, frame):
        widgets = self.entry_widgets[id(entry)]
        new_day = widgets['inline_day_var'].get()
        new_time = widgets['inline_time_entry'].get()
        new_song = widgets['inline_song_var'].get()

        if len(new_time.split(':')) == 2 and all(c.isdigit() for c in "".join(new_time.split(':'))):
            entry['day'] = new_day
            entry['time'] = new_time
            entry['song'] = new_song if new_song != "Случайна" else None
            widgets['inline_day_menu'].destroy()
            widgets['inline_time_entry'].destroy()
            widgets['inline_song_menu'].destroy()
            self.populate_editor()
        else:
            print("Invalid time format for inline edit")

    def add_schedule_entry(self):
        day = self.day_var.get()
        new_time = self.time_entry.get()
        song = self.song_var.get()
        if len(new_time.split(':')) == 2 and all(c.isdigit() for c in "".join(new_time.split(':'))):
            self.temp_schedule.append({'day': day, 'time': new_time, 'song': song if song != "Случайна" else None})
            self.time_entry.delete(0, 'end')
            self.populate_editor()
        else:
            print("Invalid time format for new entry")

    def delete_schedule_entry(self, entry, frame):
        self.temp_schedule.remove(entry)
        frame.destroy()

    def save_and_close(self):
        self.parent_app.update_schedule(self.temp_schedule)
        self.destroy()

    def cancel(self):
        self.destroy()

class SchoolBellApp(customtkinter.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(APP_NAME)
        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.resizable(False, False)
        customtkinter.set_appearance_mode("dark")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.editor_window = None
        self.songs_window = None
        self.last_csv_mod_time = 0

        if not os.path.exists(RESOURCES_DIR):
            os.makedirs(RESOURCES_DIR)

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

        self.bell_times = self.load_schedule()
        self.log_message("Приложението е готово. Натиснете 'СТАРТ'.")
        
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
                self.log_message("Открита е промяна в schedule.csv. Презареждане...")
                self.reload_schedule_from_csv()
            self.last_csv_mod_time = mod_time
        except FileNotFoundError:
            pass # Handled by load_schedule

        # Schedule next update
        self.after(1000, self.start_ui_update_loops)

    def reload_schedule_from_csv(self):
        self.bell_times = self.load_schedule()
        self.log_message("Програмата е презаредена от CSV файла.")
        if self.service_running:
            self.log_message("Рестартиране на услугата с новата програма...")
            self.stop_service()
            self.start_service()

    def setup_left_panel(self):
        self.left_panel = customtkinter.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nswe", padx=20, pady=20)
        self.left_panel.grid_rowconfigure(6, weight=1) 
        customtkinter.CTkLabel(self.left_panel, text="СТАТУС:", font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")
        self.status_label = customtkinter.CTkLabel(self.left_panel, text="СПРЯН", text_color=RED, font=customtkinter.CTkFont(size=18, weight="bold"))
        self.status_label.grid(row=1, column=0, padx=20, pady=5, sticky="w")
        
        customtkinter.CTkLabel(self.left_panel, text="Текущо време:", font=customtkinter.CTkFont(size=16)).grid(row=2, column=0, padx=20, pady=(20, 5), sticky="w")
        self.digital_clock_label = customtkinter.CTkLabel(self.left_panel, text="--:--:--", font=customtkinter.CTkFont(size=18, weight="bold"))
        self.digital_clock_label.grid(row=3, column=0, padx=20, pady=5, sticky="w")

        customtkinter.CTkLabel(self.left_panel, text="Следващ звънец:", font=customtkinter.CTkFont(size=16)).grid(row=4, column=0, padx=20, pady=(20, 5), sticky="w")
        self.next_bell_label = customtkinter.CTkLabel(self.left_panel, text="--:--:--", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.next_bell_label.grid(row=5, column=0, padx=20, pady=5, sticky="w")
        
        self.start_stop_button = customtkinter.CTkButton(self.left_panel, text="СТАРТ", command=self.toggle_service)
        self.start_stop_button.grid(row=7, column=0, padx=20, pady=20, sticky="ew")
        
        
        
    def update_digital_clock(self):
        self.digital_clock_label.configure(text=datetime.now().strftime("%H:%M:%S"))

    def setup_center_panel(self):
        self.center_panel = customtkinter.CTkFrame(self, fg_color="transparent")
        self.center_panel.grid(row=0, column=1, sticky="nswe", padx=0, pady=20)
        self.center_panel.grid_rowconfigure(0, weight=1)
        self.center_panel.grid_columnconfigure(0, weight=1)
        self.log_box = Text(self.center_panel, wrap=WORD, state="disabled", bg="#2B2B2B", fg="white", bd=0, font=("Consolas", 11))
        self.log_box.grid(row=0, column=0, sticky="nswe")

    def setup_right_panel(self):
        self.right_panel = customtkinter.CTkFrame(self, fg_color="transparent")
        self.right_panel.grid(row=0, column=2, sticky="nswe", padx=20, pady=20)
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        self.schedule_display_title = customtkinter.CTkLabel(self.right_panel, text="", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.schedule_display_title.grid(row=0, column=0, padx=10, pady=(10, 10), sticky="w")
        self.schedule_display_frame = customtkinter.CTkScrollableFrame(self.right_panel, fg_color="transparent")
        self.schedule_display_frame.grid(row=1, column=0, sticky="nsew", padx=10)
        self.edit_button = customtkinter.CTkButton(self.right_panel, text="Редактирай програмата", command=self.open_schedule_editor)
        self.edit_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    def populate_schedule_display(self):
        for widget in self.schedule_display_frame.winfo_children():
            widget.destroy()
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
            
    def update_schedule(self, new_schedule):
        self.bell_times = new_schedule
        self.save_schedule(self.bell_times)
        self.log_message("Програмата беше обновена.")
        if self.service_running:
            self.log_message("Рестартиране на услугата с новата програма...")
            self.stop_service()
            self.start_service()

    def load_schedule(self):
        schedule_data = []
        try:
            self.last_csv_mod_time = os.path.getmtime(SCHEDULE_FILE)
            with open(SCHEDULE_FILE, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                fieldnames = reader.fieldnames
                for row in reader:
                    entry = {'day': row['Ден'], 'time': row['Час']}
                    if 'Песен' in fieldnames:
                        entry['song'] = row.get('Песен') if row.get('Песен') else None
                    else:
                        entry['song'] = None
                    schedule_data.append(entry)
        except FileNotFoundError:
            self.log_message(f"[ИНФО] {SCHEDULE_FILE} не е намерен, създавам нов.")
            self.save_schedule([])
        except Exception as e:
            self.log_message(f"[ГРЕШКА] при зареждане на {SCHEDULE_FILE}: {e}")
        return schedule_data

    def save_schedule(self, schedule_data):
        try:
            with open(SCHEDULE_FILE, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['Ден', 'Час', 'Песен'])
                writer.writeheader()
                writer.writerows([{'Ден': r['day'], 'Час': r['time'], 'Песен': r.get('song')} for r in schedule_data])
            self.last_csv_mod_time = os.path.getmtime(SCHEDULE_FILE)
        except Exception as e:
            self.log_message(f"[ГРЕШКА] при запазване на {SCHEDULE_FILE}: {e}")

    def log_message(self, msg):
        self.after(0, lambda: self._log_thread_safe(msg))

    def _log_thread_safe(self, msg):
        now = datetime.now().strftime("%H:%M:%S")
        self.log_box.config(state="normal")
        self.log_box.insert(END, f"[{now}] {msg}\n")
        self.log_box.config(state="disabled")
        self.log_box.see(END)

    def toggle_service(self):
        if self.service_running: self.stop_service()
        else: self.start_service()

    def start_service(self):
        self.service_running = True
        self.log_message("Услугата стартира...")
        self.status_label.configure(text="РАБОТИ", text_color=GREEN)
        self.start_stop_button.configure(text="СТОП")
        self.edit_button.configure(state="disabled")
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def stop_service(self):
        self.service_running = False
        schedule.clear()
        if mixer.music.get_busy(): mixer.music.stop()
        self.status_label.configure(text="СПРЯН", text_color=RED)
        self.start_stop_button.configure(text="СТАРТ")
        self.next_bell_label.configure(text="--:--:--")
        self.edit_button.configure(state="normal")
        self.log_message("Услугата е спряна.")

    def run_scheduler(self):
        self.log_message("Планиране на задачите...")
        schedule.clear()
        for job in self.bell_times:
            day_en = DAY_MAP_BG_TO_EN.get(job['day'])
            if day_en:
                try:
                    getattr(schedule.every(), day_en).at(job['time']).do(self.play_song, song_name=job.get('song'))
                except Exception as e:
                    self.log_message(f"[ГРЕШКА] Невалидна задача: {job['day']} в {job['time']}. Грешка: {e}")
        
        self.log_message("Всички задачи са планирани.")
        
        # self.after(0, self.update_next_bell_label) # Handled by start_ui_update_loops

        while self.service_running:
            schedule.run_pending()
            time.sleep(1)

    def update_next_bell_label(self):
        if self.service_running:
            if schedule and schedule.jobs:
                next_run_val = schedule.next_run()
                if next_run_val:
                    day_text = BG_WEEKDAYS[next_run_val.weekday()]
                    self.next_bell_label.configure(text=f"{day_text} в {next_run_val.strftime('%H:%M:%S')}")
                else:
                    self.next_bell_label.configure(text="Няма предстоящи")
            else:
                self.next_bell_label.configure(text="Няма планирани")
            
            # self.after(1000, self.update_next_bell_label) # Handled by start_ui_update_loops

    def play_song(self, song_name=None):
        self.log_message("Време е за звънец! Търсене на песен...")
        try:
            song_list = [s for s in os.listdir(RESOURCES_DIR) if s.endswith((".mp3", ".wav", ".ogg"))]
            if not song_list:
                self.log_message(f"[ГРЕШКА] Няма песни в '{RESOURCES_DIR}'.")
                return schedule.CancelJob
            
            song_to_play = None
            if song_name and song_name in song_list:
                song_to_play = song_name
            else:
                song_to_play = random.choice(song_list)

            local_path = os.path.join(RESOURCES_DIR, song_to_play)
            
            self.log_message(f"Пускане на '{song_to_play}'...")
            mixer.music.load(local_path)
            mixer.music.play()
            
            while mixer.music.get_busy() and self.service_running:
                time.sleep(0.5)

        except Exception as e:
            self.log_message(f"[ГРЕШКА] Проблем при пускане на песен: {e}")
        return schedule.CancelJob

    def on_closing(self):
        if self.service_running: self.stop_service()
        if self.editor_window: self.editor_window.destroy()
        if self.songs_window: self.songs_window.destroy()
        self.destroy()

if __name__ == "__main__":
    app = SchoolBellApp()
    app.mainloop()

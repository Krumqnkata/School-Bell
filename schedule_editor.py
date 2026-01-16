"""
Schedule editor window for the School Bell application.
"""
import customtkinter
import os
from config import DAYS_OF_WEEK, BG_WEEKDAYS
from utils import save_schedule
import csv


class ScheduleEditorWindow(customtkinter.CTkToplevel):
    def __init__(self, parent_app):
        super().__init__(parent_app)
        self.parent_app = parent_app
        self.title("Редактор на програмата")
        self.geometry("700x750")
        self.resizable(True, True)
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

        from config import RESOURCES_DIR
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

            edit_button = customtkinter.CTkButton(frame, text="Промени", width=70, fg_color="#3a7ebf", command=lambda e=entry, f=frame: self.toggle_inline_edit(e, f))
            edit_button.grid(row=0, column=2, padx=5)
            delete_button = customtkinter.CTkButton(frame, text="Изтрий", width=60, fg_color="#E84545", command=lambda e=entry, f=frame: self.delete_schedule_entry(e, f))
            delete_button.grid(row=0, column=3, padx=5)
            self.entry_widgets[entry_id] = {'frame': frame, 'label': label, 'edit_button': edit_button}

    def toggle_inline_edit(self, entry, frame):
        widgets = self.entry_widgets[id(entry)]
        widgets['label'].grid_forget()
        widgets['edit_button'].configure(text="Запази", fg_color="#2CC985", command=lambda e=entry, f=frame: self.save_inline_edit(e, f))

        inline_day_var = customtkinter.StringVar(value=entry['day'])
        inline_day_menu = customtkinter.CTkOptionMenu(frame, variable=inline_day_var, values=DAYS_OF_WEEK, width=120)
        inline_day_menu.grid(row=0, column=0, sticky="w", padx=5)

        inline_time_entry = customtkinter.CTkEntry(frame, width=60)
        inline_time_entry.insert(0, entry['time'])
        inline_time_entry.grid(row=0, column=1, sticky="w", padx=5)

        current_song = entry.get('song') if entry.get('song') else "Случайна"
        inline_song_var = customtkinter.StringVar(value=current_song)
        from config import RESOURCES_DIR
        song_list = ["Случайна"] + [s for s in os.listdir(RESOURCES_DIR) if s.endswith((".mp3", ".wav", ".ogg"))]
        inline_song_menu = customtkinter.CTkOptionMenu(frame, variable=inline_song_var, values=song_list, width=140)
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
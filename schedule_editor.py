"""
Schedule editor window for the School Bell application.
"""
import customtkinter
import os
from config import DAYS_OF_WEEK, BG_WEEKDAYS, NORMAL_SCHEDULE_FILE, ALTERNATIVE_SCHEDULE_FILE
from utils import save_schedule, _read_schedule_file, save_specific_schedule
import csv


class ScheduleEditorWindow(customtkinter.CTkToplevel):
    def __init__(self, parent_app, schedule_type="normal"):
        super().__init__(parent_app)
        self.parent_app = parent_app
        self.schedule_type = schedule_type
        self.title(f"Редактор на програмата ({'Нормален' if schedule_type == 'normal' else 'Алтернативен'})")
        self.geometry("700x600")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.transient(parent_app)

        # Determine which file to load based on schedule_type
        if self.schedule_type == "normal":
            self.schedule_filepath = NORMAL_SCHEDULE_FILE
        else:
            self.schedule_filepath = ALTERNATIVE_SCHEDULE_FILE

        # Configure grid weights for resizing - remove empty spaces
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Main container frame with minimal padding
        main_container = customtkinter.CTkFrame(self)
        main_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        main_container.grid_rowconfigure(1, weight=1)  # Give weight to content area
        main_container.grid_columnconfigure(0, weight=1)

        # Create notebook-style tabs for better organization
        self.tab_view = customtkinter.CTkTabview(main_container)
        self.tab_view.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.tab_view.grid_rowconfigure(0, weight=1)
        self.tab_view.grid_columnconfigure(0, weight=1)

        # Create tabs
        self.edit_tab = self.tab_view.add("Редактиране")
        self.copy_tab = self.tab_view.add("Копиране")

        # Setup editing tab
        self.setup_edit_tab()

        # Setup copying tab
        self.setup_copy_tab()

        # Buttons frame at the bottom of the main container
        buttons_frame = customtkinter.CTkFrame(main_container)
        buttons_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 0))
        buttons_frame.grid_columnconfigure((0, 1), weight=1)

        # Action buttons
        save_button = customtkinter.CTkButton(buttons_frame, text="Запази и затвори", fg_color="#2CC985", hover_color="#24a66d", command=self.save_and_close)
        save_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        cancel_button = customtkinter.CTkButton(buttons_frame, text="Отказ", fg_color="#E84545", hover_color="#c53232", command=self.cancel)
        cancel_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Initialize temp_schedule by loading from the determined file
        self.temp_schedule = _read_schedule_file(self.schedule_filepath)

        # Populate the editor
        self.populate_editor()

    def setup_edit_tab(self):
        """Setup the editing tab with clear sections"""
        # Configure grid for the edit tab
        self.edit_tab.grid_rowconfigure(0, weight=1)
        self.edit_tab.grid_columnconfigure(0, weight=1)

        # Container for the edit tab content
        edit_container = customtkinter.CTkFrame(self.edit_tab)
        edit_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        edit_container.grid_rowconfigure(3, weight=1)  # Changed to row 3 to account for new row
        edit_container.grid_columnconfigure(0, weight=1)

        # Day selector frame
        day_selector_frame = customtkinter.CTkFrame(edit_container, fg_color="transparent")
        day_selector_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        day_selector_frame.grid_columnconfigure(2, weight=1)  # Updated to account for new column

        customtkinter.CTkLabel(day_selector_frame, text="Избери ден:").grid(row=0, column=0, padx=(0, 10), sticky="w")
        self.selected_day_var = customtkinter.StringVar(value=DAYS_OF_WEEK[0])
        self.day_selector = customtkinter.CTkOptionMenu(
            day_selector_frame,
            variable=self.selected_day_var,
            values=DAYS_OF_WEEK,
            width=150,
            command=lambda choice: self.on_day_change()
        )
        self.day_selector.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        # Select/Deselect all button
        self.select_all_var = customtkinter.BooleanVar()
        self.select_all_checkbox = customtkinter.CTkCheckBox(
            day_selector_frame,
            text="Селектирай всички",
            variable=self.select_all_var,
            command=self.toggle_select_all
        )
        self.select_all_checkbox.grid(row=0, column=2, sticky="e", padx=(10, 0))

        # Bulk edit frame for selected entries
        bulk_edit_frame = customtkinter.CTkFrame(edit_container, fg_color="transparent")
        bulk_edit_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        bulk_edit_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(bulk_edit_frame, text="Масово редактиране на селектирани записи:").grid(row=0, column=0, padx=(0, 5), sticky="w")

        from config import RESOURCES_DIR
        bulk_song_list = ["Случайна"] + [s for s in os.listdir(RESOURCES_DIR) if s.endswith((".mp3", ".wav", ".ogg"))]
        self.bulk_song_var = customtkinter.StringVar(value=bulk_song_list[0])
        bulk_song_option = customtkinter.CTkOptionMenu(bulk_edit_frame, variable=self.bulk_song_var, values=bulk_song_list, width=140)
        bulk_song_option.grid(row=0, column=1, sticky="w", padx=(0, 10))

        # Bulk edit button
        bulk_edit_button = customtkinter.CTkButton(bulk_edit_frame, text="Редактирай селектирани", width=120,
                                                 fg_color="#8B4513", hover_color="#A0522D", command=self.bulk_edit_selected_songs)
        bulk_edit_button.grid(row=0, column=2, padx=(5,0))

        # Scrollable frame for schedule entries
        self.editor_frame = customtkinter.CTkScrollableFrame(edit_container, label_text="Програма за избрания ден", height=300)
        self.editor_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.editor_frame.grid_columnconfigure(0, weight=1)

        # Add entry frame
        add_frame = customtkinter.CTkFrame(edit_container)
        add_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=10)
        add_frame.grid_columnconfigure(1, weight=1)

        # Labels for the input fields (without day since it's selected separately)
        customtkinter.CTkLabel(add_frame, text="Час:").grid(row=0, column=0, padx=(0,5), sticky="w")
        customtkinter.CTkLabel(add_frame, text="Песен:").grid(row=0, column=2, padx=(10,5), sticky="w")

        # Input fields (without day since it's selected separately)
        self.time_entry = customtkinter.CTkEntry(add_frame, placeholder_text="HH:MM", width=100)
        self.time_entry.grid(row=0, column=1, sticky="w", padx=(0, 10))

        from config import RESOURCES_DIR
        self.song_list = ["Случайна"] + [s for s in os.listdir(RESOURCES_DIR) if s.endswith((".mp3", ".wav", ".ogg"))]
        self.song_var = customtkinter.StringVar(value=self.song_list[0])
        song_option = customtkinter.CTkOptionMenu(add_frame, variable=self.song_var, values=self.song_list, width=140)
        song_option.grid(row=0, column=3, sticky="w", padx=(0, 10))

        # Add button
        add_button = customtkinter.CTkButton(add_frame, text="Добави запис", width=80, command=self.add_schedule_entry)
        add_button.grid(row=0, column=4, padx=(5,0))

    def setup_copy_tab(self):
        """Setup the copying tab with clear organization"""
        # Configure grid for the copy tab
        self.copy_tab.grid_rowconfigure(0, weight=1)
        self.copy_tab.grid_columnconfigure(0, weight=1)

        # Container for the copy tab content
        copy_container = customtkinter.CTkFrame(self.copy_tab)
        copy_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        copy_container.grid_rowconfigure(0, weight=1)
        copy_container.grid_columnconfigure(0, weight=1)

        # Create notebook-style tabs for copy operations
        copy_tabview = customtkinter.CTkTabview(copy_container)
        copy_tabview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        copy_tabview.grid_rowconfigure(0, weight=1)
        copy_tabview.grid_columnconfigure(0, weight=1)

        # Create tabs for different bulk operations
        copy_schedule_tab = copy_tabview.add("Копиране на програма")

        # Setup copy schedule tab
        self.setup_copy_schedule_tab(copy_schedule_tab)


    def setup_copy_schedule_tab(self, parent_frame):
        """Setup the copy schedule tab"""
        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)

        # Main frame for copy schedule content
        bulk_edit_frame = customtkinter.CTkFrame(parent_frame, fg_color="transparent")
        bulk_edit_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        bulk_edit_frame.grid_columnconfigure(1, weight=1)

        # Title for the copy section
        title_label = customtkinter.CTkLabel(bulk_edit_frame, text="Копиране на програма между дни",
                                           font=customtkinter.CTkFont(size=16, weight="bold"))
        title_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # Description
        desc_label = customtkinter.CTkLabel(bulk_edit_frame, text="Изберете изходен ден и целиеви дни за копиране на цялата програма",
                                          font=customtkinter.CTkFont(size=12))
        desc_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 15))

        # Source day selection
        source_frame = customtkinter.CTkFrame(bulk_edit_frame, fg_color="transparent")
        source_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        source_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(source_frame, text="Копирай програмата от:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.bulk_source_day_var = customtkinter.StringVar(value=DAYS_OF_WEEK[0])
        customtkinter.CTkOptionMenu(source_frame, variable=self.bulk_source_day_var, values=DAYS_OF_WEEK, width=150).grid(row=0, column=1, sticky="w")

        # Target days selection
        target_frame = customtkinter.CTkFrame(bulk_edit_frame, fg_color="transparent")
        target_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=10)

        customtkinter.CTkLabel(target_frame, text="Копирай в следните дни:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=(5,0))

        self.bulk_target_day_vars = {}
        checkboxes_frame = customtkinter.CTkFrame(target_frame, fg_color="transparent")
        checkboxes_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)

        # Arrange checkboxes in a grid (2 rows of 4 columns for 7 days)
        for i, day in enumerate(DAYS_OF_WEEK):
            var = customtkinter.StringVar()
            cb = customtkinter.CTkCheckBox(checkboxes_frame, text=day, variable=var, onvalue=day, offvalue="")
            row_idx = i // 4
            col_idx = i % 4
            cb.grid(row=row_idx, column=col_idx, padx=5, pady=2, sticky="w")
            self.bulk_target_day_vars[day] = var

        # Copy button
        copy_button = customtkinter.CTkButton(bulk_edit_frame, text="Копирай програмата", width=120,
                                            fg_color="#3a7ebf", hover_color="#2a6bbf", command=self.bulk_copy_schedule)
        copy_button.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(20,0))

        # Info text
        info_label = customtkinter.CTkLabel(bulk_edit_frame, text="Забележка: Копирането ще замени цялата програма за избраните дни!",
                                         font=customtkinter.CTkFont(size=11), text_color="orange")
        info_label.grid(row=5, column=0, columnspan=3, sticky="w", pady=(10,0))

    def setup_bulk_edit_songs_tab(self, parent_frame):
        """Setup the bulk edit songs tab"""
        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)

        # Main frame for bulk edit songs content
        bulk_edit_songs_frame = customtkinter.CTkFrame(parent_frame, fg_color="transparent")
        bulk_edit_songs_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        bulk_edit_songs_frame.grid_columnconfigure(1, weight=1)

        # Title for the bulk edit songs section
        title_label = customtkinter.CTkLabel(bulk_edit_songs_frame, text="Масово редактиране на песни",
                                           font=customtkinter.CTkFont(size=16, weight="bold"))
        title_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # Description
        desc_label = customtkinter.CTkLabel(bulk_edit_songs_frame, text="Изберете дни и нова песен, за да замените всички песни за тези дни",
                                          font=customtkinter.CTkFont(size=12))
        desc_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 15))

        # Days selection
        days_frame = customtkinter.CTkFrame(bulk_edit_songs_frame, fg_color="transparent")
        days_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        customtkinter.CTkLabel(days_frame, text="Изберете дни:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=(5,0))

        self.bulk_edit_song_day_vars = {}
        checkboxes_frame = customtkinter.CTkFrame(days_frame, fg_color="transparent")
        checkboxes_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)

        # Arrange checkboxes in a grid (2 rows of 4 columns for 7 days)
        for i, day in enumerate(DAYS_OF_WEEK):
            var = customtkinter.StringVar()
            cb = customtkinter.CTkCheckBox(checkboxes_frame, text=day, variable=var, onvalue=day, offvalue="")
            row_idx = i // 4
            col_idx = i % 4
            cb.grid(row=row_idx, column=col_idx, padx=5, pady=2, sticky="w")
            self.bulk_edit_song_day_vars[day] = var

        # Song selection
        song_selection_frame = customtkinter.CTkFrame(bulk_edit_songs_frame, fg_color="transparent")
        song_selection_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=10)

        customtkinter.CTkLabel(song_selection_frame, text="Нова песен:").grid(row=0, column=0, sticky="w", padx=(0, 5))

        from config import RESOURCES_DIR
        self.bulk_edit_song_list = ["Случайна"] + [s for s in os.listdir(RESOURCES_DIR) if s.endswith((".mp3", ".wav", ".ogg"))]
        self.bulk_edit_song_var = customtkinter.StringVar(value=self.bulk_edit_song_list[0])
        song_option = customtkinter.CTkOptionMenu(song_selection_frame, variable=self.bulk_edit_song_var, values=self.bulk_edit_song_list, width=140)
        song_option.grid(row=0, column=1, sticky="w", padx=(0, 10))

        # Bulk edit songs button
        bulk_edit_button = customtkinter.CTkButton(bulk_edit_songs_frame, text="Замени песните", width=120,
                                                 fg_color="#8B4513", hover_color="#A0522D", command=self.bulk_edit_songs)
        bulk_edit_button.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(20,0))

        # Info text
        info_label = customtkinter.CTkLabel(bulk_edit_songs_frame, text="Забележка: Това ще замени всички песни за избраните дни!",
                                         font=customtkinter.CTkFont(size=11), text_color="orange")
        info_label.grid(row=5, column=0, columnspan=3, sticky="w", pady=(10,0))

    def bulk_edit_songs(self):
        """Bulk edit songs for selected days"""
        selected_days = [var.get() for var in self.bulk_edit_song_day_vars.values() if var.get()]
        new_song = self.bulk_edit_song_var.get()

        if not selected_days:
            return

        # Process each selected day
        for day in selected_days:
            # Get all entries for this day
            day_entries = [entry for entry in self.temp_schedule if entry['day'] == day]

            # Update the song for each entry
            for entry in day_entries:
                if new_song == "Случайна":
                    entry['song'] = None  # Will trigger random song
                else:
                    entry['song'] = new_song

        # Refresh the display
        self.populate_editor()
        # If currently viewing one of the modified days, update the display
        if self.selected_day_var.get() in selected_days:
            self.populate_editor()

    def bulk_copy_schedule(self):
        source_day = self.bulk_source_day_var.get()
        target_days = [var.get() for var in self.bulk_target_day_vars.values() if var.get()]

        if not target_days:
            return

        source_schedule = [entry for entry in self.temp_schedule if entry['day'] == source_day]

        # Remove existing entries for target days from temp_schedule
        filtered_temp = [entry for entry in self.temp_schedule if entry['day'] not in target_days]

        # Add copied entries
        for day in target_days:
            for source_entry in source_schedule:
                new_entry = source_entry.copy()
                new_entry['day'] = day
                filtered_temp.append(new_entry)

        self.temp_schedule = filtered_temp
        self.populate_editor()

    def on_day_change(self, *args):
        """Callback when the selected day changes"""
        # Update the view to show entries for the selected day
        self.populate_editor()

    def populate_editor(self):
        for widget in self.editor_frame.winfo_children():
            widget.destroy()

        # Get the selected day
        selected_day = self.selected_day_var.get()

        # Filter entries for the selected day
        day_entries = [entry for entry in self.temp_schedule if entry['day'] == selected_day]
        day_entries.sort(key=lambda x: x['time'])  # Sort by time only since all entries are for the same day

        self.entry_widgets = {}
        for entry in day_entries:
            entry_id = id(entry)
            frame = customtkinter.CTkFrame(self.editor_frame)
            frame.pack(fill="x", padx=5, pady=5)
            frame.grid_columnconfigure(0, weight=1)

            # Create a sub-frame for the content to better align elements
            content_frame = customtkinter.CTkFrame(frame, fg_color="transparent")
            content_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
            content_frame.grid_columnconfigure(0, weight=1)

            # Add checkbox for bulk selection
            checkbox_var = customtkinter.BooleanVar()
            checkbox = customtkinter.CTkCheckBox(content_frame, text="", variable=checkbox_var, width=20)
            checkbox.grid(row=0, column=0, sticky="w", padx=(0, 5))

            song_display = entry.get('song') if entry.get('song') else "Случайна"
            label = customtkinter.CTkLabel(content_frame, text=f"{entry['time']} ({song_display})", anchor="w")
            label.grid(row=0, column=1, sticky="ew", padx=(0, 10))

            # Button frame for edit/delete buttons
            button_frame = customtkinter.CTkFrame(content_frame, fg_color="transparent")
            button_frame.grid(row=0, column=2, sticky="e")

            edit_button = customtkinter.CTkButton(button_frame, text="Промени", width=70, fg_color="#3a7ebf", command=lambda e=entry, f=frame: self.toggle_inline_edit(e, f))
            edit_button.grid(row=0, column=0, padx=2)
            delete_button = customtkinter.CTkButton(button_frame, text="Изтрий", width=70, fg_color="#E84545", command=lambda e=entry, f=frame: self.delete_schedule_entry(e, f))
            delete_button.grid(row=0, column=1, padx=2)

            self.entry_widgets[entry_id] = {
                'frame': frame,
                'label': label,
                'edit_button': edit_button,
                'checkbox': checkbox,
                'checkbox_var': checkbox_var,
                'entry': entry
            }

    def toggle_inline_edit(self, entry, frame):
        widgets = self.entry_widgets[id(entry)]

        # Remove the original label
        widgets['label'].grid_forget()

        # Change the edit button to save button
        widgets['edit_button'].configure(text="Запази", fg_color="#2CC985", command=lambda e=entry, f=frame: self.save_inline_edit(e, f))

        # Get the content frame inside the main frame
        content_frame = frame.winfo_children()[0]  # This should be the content_frame

        # Create a temporary frame for editing controls
        edit_frame = customtkinter.CTkFrame(content_frame, fg_color="transparent")
        edit_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        edit_frame.grid_columnconfigure(0, weight=1)

        # Create editing controls
        inline_time_entry = customtkinter.CTkEntry(edit_frame, width=80)
        inline_time_entry.insert(0, entry['time'])
        inline_time_entry.grid(row=0, column=0, sticky="w", padx=(0, 5))

        current_song = entry.get('song') if entry.get('song') else "Случайна"
        inline_song_var = customtkinter.StringVar(value=current_song)
        from config import RESOURCES_DIR
        song_list = ["Случайна"] + [s for s in os.listdir(RESOURCES_DIR) if s.endswith((".mp3", ".wav", ".ogg"))]
        inline_song_menu = customtkinter.CTkOptionMenu(edit_frame, variable=inline_song_var, values=song_list, width=120)
        inline_song_menu.grid(row=0, column=1, sticky="w", padx=(0, 10))

        # Button frame for the save button
        button_frame = customtkinter.CTkFrame(edit_frame, fg_color="transparent")
        button_frame.grid(row=0, column=2, sticky="e")

        # Store references to the editing widgets
        widgets['edit_frame'] = edit_frame
        widgets['inline_time_entry'] = inline_time_entry
        widgets['inline_song_var'] = inline_song_var
        widgets['inline_song_menu'] = inline_song_menu

    def save_inline_edit(self, entry, frame):
        widgets = self.entry_widgets[id(entry)]
        new_time = widgets['inline_time_entry'].get()
        new_song = widgets['inline_song_var'].get()

        if len(new_time.split(':')) == 2 and all(c.isdigit() for c in "".join(new_time.split(':'))):
            entry['time'] = new_time
            entry['song'] = new_song if new_song != "Случайна" else None
            # Clean up the editing widgets
            widgets['edit_frame'].destroy()
            self.populate_editor()
        else:
            print("Invalid time format for inline edit")

    def toggle_select_all(self):
        """Toggle selection of all entries"""
        select_all = self.select_all_var.get()
        for entry_id, widgets in self.entry_widgets.items():
            widgets['checkbox_var'].set(select_all)

    def bulk_edit_selected_songs(self):
        """Bulk edit songs for selected entries"""
        selected_entries = []
        for entry_id, widgets in self.entry_widgets.items():
            if widgets['checkbox_var'].get():
                selected_entries.append(widgets['entry'])

        if not selected_entries:
            return

        new_song = self.bulk_song_var.get()
        for entry in selected_entries:
            if new_song == "Случайна":
                entry['song'] = None  # Will trigger random song
            else:
                entry['song'] = new_song

        # Refresh the display
        self.populate_editor()

    def on_day_change(self, *args):
        """Callback when the selected day changes"""
        # Reset the select all checkbox when changing days
        self.select_all_var.set(False)
        # Update the view to show entries for the selected day
        self.populate_editor()

    def add_schedule_entry(self):
        day = self.selected_day_var.get()  # Use the selected day from the dropdown
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

    def bulk_copy_schedule(self):
        source_day = self.bulk_source_day_var.get()
        target_days = [var.get() for var in self.bulk_target_day_vars.values() if var.get()]

        if not target_days:
            return

        source_schedule = [entry for entry in self.temp_schedule if entry['day'] == source_day]

        # Remove existing entries for target days from temp_schedule
        filtered_temp = [entry for entry in self.temp_schedule if entry['day'] not in target_days]

        # Add copied entries
        for day in target_days:
            for source_entry in source_schedule:
                new_entry = source_entry.copy()
                new_entry['day'] = day
                filtered_temp.append(new_entry)

        self.temp_schedule = filtered_temp
        self.populate_editor()

    def save_and_close(self):
        save_specific_schedule(self.schedule_filepath, self.temp_schedule)
        self.parent_app.reload_schedule_from_csv() # Trigger reload in main app
        self.destroy()

    def cancel(self):
        self.destroy()
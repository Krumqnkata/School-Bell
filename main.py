"""
Main application class for the School Bell application.
Contains the main GUI and core functionality.
"""
import customtkinter
import threading
import time
from tkinter import *
import os
from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify
import shared_state
from pygame import mixer
from datetime import datetime
from config import APP_NAME, WIDTH, HEIGHT, RESOURCES_DIR, SCHEDULE_FILE, DAYS_OF_WEEK
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
        self.start_web_panel()

    def start_web_panel(self):
        """Starts the Flask web panel in a separate thread."""
        def run_flask():
            # Running with debug=False and use_reloader=False is crucial for threaded apps
            flask_app.run(port=1927, host='0.0.0.0', debug=False, use_reloader=False)

        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True  # Allows main app to exit even if this thread is running
        flask_thread.start()
        self.log_message("Уеб панелът е стартиран на http://127.0.0.1:1927")

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

# --- Web Panel ---
flask_app = Flask(__name__, template_folder='web_panel/templates')
flask_app.secret_key = 'supersecretkey_for_schoolbell'

def get_song_list():
    """Returns a list of available songs."""
    try:
        return [s for s in os.listdir(RESOURCES_DIR) if s.endswith((".mp3", ".wav", ".ogg"))]
    except FileNotFoundError:
        return []

@flask_app.route('/')
def index():
    """Main page, displays the schedule."""
    schedule = load_schedule()
    schedule.sort(key=lambda x: (DAYS_OF_WEEK.index(x['day']), x['time']))
    songs = get_song_list()
    return render_template('index.html', schedule=schedule, days_of_week=DAYS_OF_WEEK, songs=songs)

@flask_app.route('/add', methods=['POST'])
def add_entry():
    """Adds a new entry to the schedule."""
    day = request.form.get('day')
    time = request.form.get('time')
    song = request.form.get('song')

    if not day or not time or not song:
        flash('Моля, попълнете всички полета.', 'error')
        return redirect(url_for('index'))

    try:
        hour, minute = map(int, time.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Invalid time range")
    except ValueError:
        flash('Невалиден формат за час. Моля, използвайте HH:MM.', 'error')
        return redirect(url_for('index'))

    schedule = load_schedule()
    if any(entry['day'] == day and entry['time'] == time for entry in schedule):
        flash('Такъв запис вече съществува.', 'warning')
        return redirect(url_for('index'))

    schedule.append({'day': day, 'time': time, 'song': song if song != "Случайна" else None})
    save_schedule(schedule)
    flash('Записът е добавен успешно.', 'success')
    return redirect(url_for('index'))

@flask_app.route('/delete', methods=['POST'])
def delete_entry():
    """Deletes an entry from the schedule."""
    day_to_delete = request.form.get('day')
    time_to_delete = request.form.get('time')

    if not day_to_delete or not time_to_delete:
        flash('Липсва информация за изтриване на записа.', 'error')
        return redirect(url_for('index'))

    schedule = load_schedule()
    entry_found = False
    new_schedule = []
    for entry in schedule:
        if not (entry['day'] == day_to_delete and entry['time'] == time_to_delete and not entry_found):
            new_schedule.append(entry)
        else:
            entry_found = True
            
    if entry_found:
        save_schedule(new_schedule)
        flash('Записът е изтрит успешно.', 'success')
    else:
        flash('Записът за изтриване не е намерен.', 'error')

    return redirect(url_for('index'))


@flask_app.route('/play', methods=['POST'])
def play_sound_web():
    """Plays a sound file via a web request, respecting quiet mode."""
    # Check for quiet mode first
    if shared_state.gui_app and shared_state.gui_app.quiet_mode.get():
        message = "Не може да се пусне ръчен звънец, защото 'Тих режим' е активен."
        log_message(shared_state.gui_app, f"[WEB] {message}")
        return jsonify({'status': 'warning', 'message': message})

    song_name = request.form.get('song')
    if not song_name:
        return jsonify({'status': 'error', 'message': 'Липсва име на песен.'}), 400

    # Security: Ensure song_name is just a filename
    if '..' in song_name or '/' in song_name or '\\' in song_name:
        return jsonify({'status': 'error', 'message': 'Невалидно име на песен.'}), 400
        
    songs = get_song_list()
    if song_name not in songs:
        return jsonify({'status': 'error', 'message': f"Песента '{song_name}' не е намерена."}), 404

    song_path = os.path.join(RESOURCES_DIR, song_name)
    
    try:
        log_message(shared_state.gui_app, f"[WEB] Пускане на ръчен звънец: '{song_name}'...")
        mixer.music.load(song_path)
        mixer.music.play()
        return jsonify({'status': 'success', 'message': f"Пускане на '{song_name}'..."})
    except Exception as e:
        log_message(shared_state.gui_app, f"[WEB-ERROR] Грешка при пускане на песен: {e}")
        return jsonify({'status': 'error', 'message': f"Грешка при пускане на песента: {e}"}), 500

@flask_app.route('/stop-sound', methods=['POST'])
def stop_sound_web():
    """Stops any currently playing music."""
    try:
        mixer.music.stop()
        log_message(shared_state.gui_app, "[WEB] Музиката е спряна ръчно.")
        return jsonify({'status': 'success', 'message': 'Музиката е спряна.'})
    except Exception as e:
        log_message(shared_state.gui_app, f"[WEB-ERROR] Грешка при спиране на музика: {e}")
        return jsonify({'status': 'error', 'message': f"Грешка при спиране на музиката: {e}"}), 500

@flask_app.route('/toggle-service', methods=['POST'])
def toggle_service_web():
    """Toggles the scheduler service from the web panel."""
    if shared_state.gui_app:
        shared_state.gui_app.toggle_service()
        return jsonify({'status': 'success', 'service_running': shared_state.gui_app.service_running})
    return jsonify({'status': 'error', 'message': 'GUI app not found'}), 500

@flask_app.route('/toggle-quiet-mode', methods=['POST'])
def toggle_quiet_mode_web():
    """Toggles the quiet mode from the web panel."""
    if shared_state.gui_app:
        try:
            current_state = shared_state.gui_app.quiet_mode.get()
            new_state = not current_state
            shared_state.gui_app.quiet_mode.set(new_state)
            log_message(shared_state.gui_app, f"[WEB] Тих режим е {'активиран' if new_state else 'деактивиран'}.")
            return jsonify({'status': 'success', 'quiet_mode': new_state})
        except Exception as e:
            log_message(shared_state.gui_app, f"[WEB-ERROR] Грешка при смяна на тих режим: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    return jsonify({'status': 'error', 'message': 'GUI app not found'}), 500

@flask_app.route('/status')
def status():
    """Returns the current status of the service."""
    if shared_state.gui_app:
        return jsonify({
            'service_running': shared_state.gui_app.service_running,
            'quiet_mode': shared_state.gui_app.quiet_mode.get()
        })
    return jsonify({'service_running': False, 'quiet_mode': False})


@flask_app.route('/stream-logs')
def stream_logs():
    """Streams log messages to the client using SSE."""
    def generate():
        while True:
            # Wait for a message in the queue
            log_entry = shared_state.log_queue.get()
            # Format as a Server-Sent Event
            yield f"data: {log_entry}\n\n"
    return Response(generate(), mimetype='text/event-stream')

@flask_app.route('/edit', methods=['POST'])
def edit_entry():
    """Edits an existing schedule entry."""
    original_day = request.form.get('original_day')
    original_time = request.form.get('original_time')
    
    new_day = request.form.get('day')
    new_time = request.form.get('time')
    new_song = request.form.get('song')

    if not all([original_day, original_time, new_day, new_time, new_song]):
        flash('Липсват данни за редакцията.', 'error')
        return redirect(url_for('index'))

    schedule = load_schedule()
    entry_found = False
    for entry in schedule:
        if entry['day'] == original_day and entry['time'] == original_time:
            entry['day'] = new_day
            entry['time'] = new_time
            entry['song'] = new_song if new_song != "Случайна" else None
            entry_found = True
            break
            
    if entry_found:
        save_schedule(schedule)
        flash('Записът е редактиран успешно.', 'success')
    else:
        flash('Оригиналният запис не беше намерен за редакция.', 'error')

    return redirect(url_for('index'))

    
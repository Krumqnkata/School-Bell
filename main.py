"""
Main application class for the School Bell application.
Contains the main GUI and core functionality.
"""
import customtkinter
import threading
import time
from tkinter import *
import os
from flask import Flask, render_template, request, Response, jsonify, flash, session, redirect
from werkzeug.security import check_password_hash, generate_password_hash
import shared_state
from pygame import mixer
from datetime import datetime
from config import APP_NAME, WIDTH, HEIGHT, RESOURCES_DIR, DAYS_OF_WEEK, BG_WEEKDAYS, NORMAL_SCHEDULE_FILE, ALTERNATIVE_SCHEDULE_FILE, SCHEDULE_CONFIG_FILE
from utils import load_schedule, save_schedule, log_message, load_schedule_config, save_schedule_config
from ui_components import setup_left_panel, setup_center_panel, setup_right_panel
from audio_handler import set_volume, play_song, play_song_manual
from scheduler import start_service, stop_service, run_scheduler, update_next_bell_label
from manual_handler import manual_ring
from schedule_editor import ScheduleEditorWindow
from about_dialog import AboutDialog
from tray_icon import TrayIcon
from schedule_config_editor import ScheduleConfigEditorWindow


class SchoolBellApp(customtkinter.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(APP_NAME)
        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.resizable(True, True)
        customtkinter.set_appearance_mode("dark")


        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.editor_window = None
        self.config_editor_window = None # New attribute for schedule config editor
        self.songs_window = None
        self.last_csv_mod_time = 0
        self.last_alternative_csv_mod_time = 0 # New attribute
        self.last_config_mod_time = 0 # New attribute to track schedule_config.txt mod time
        self.quiet_mode = customtkinter.BooleanVar()
        self.manual_ring_playing_thread = None # New attribute to track manual play thread
        self.background_mode = False  # Flag to track if app is in background mode

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
        mixer.music.set_volume(1.0)  # Set default volume to 100%

        self.bell_times = load_schedule()
        log_message(self, "Приложението е готово. Натиснете 'СТАРТ'.")

        # Initialize system tray icon
        self.tray_icon = TrayIcon(self)
        self.tray_icon.start_tray_icon()

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
            # Check normal schedule file
            mod_time_normal = os.path.getmtime(NORMAL_SCHEDULE_FILE)
            if self.last_csv_mod_time != 0 and mod_time_normal != self.last_csv_mod_time:
                log_message(self, f"Открита е промяна в {NORMAL_SCHEDULE_FILE}. Презареждане...")
                self.reload_schedule_from_csv()
            self.last_csv_mod_time = mod_time_normal
        except FileNotFoundError:
            pass # Handled by load_schedule
        
        try:
            # Check alternative schedule file
            mod_time_alternative = os.path.getmtime(ALTERNATIVE_SCHEDULE_FILE)
            # Use a separate last_mod_time for alternative schedule if you need to distinguish
            # For simplicity, for now, we'll just trigger reload if it changes
            if self.last_alternative_csv_mod_time != 0 and mod_time_alternative != self.last_alternative_csv_mod_time:
                log_message(self, f"Открита е промяна в {ALTERNATIVE_SCHEDULE_FILE}. Презареждане...")
                self.reload_schedule_from_csv()
            self.last_alternative_csv_mod_time = mod_time_alternative # Initialize this in __init__
        except FileNotFoundError:
            pass # Handled by load_schedule

        try:
            # Check schedule config file
            mod_time_config = os.path.getmtime(SCHEDULE_CONFIG_FILE)
            if self.last_config_mod_time != 0 and mod_time_config != self.last_config_mod_time:
                log_message(self, f"Открита е промяна в {SCHEDULE_CONFIG_FILE}. Презареждане...")
                self.reload_schedule_from_csv() # Reload main schedule
            self.last_config_mod_time = mod_time_config
        except FileNotFoundError:
            pass # Handled by load_schedule_config

        # Schedule next update
        self.after(1000, self.start_ui_update_loops)

    def reload_schedule_from_csv(self):
        self.bell_times = load_schedule()
        log_message(self, "Графикът е презареден.")
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

    def _open_schedule_editor(self, schedule_type):
        if self.editor_window is None or not self.editor_window.winfo_exists():
            self.editor_window = ScheduleEditorWindow(self, schedule_type=schedule_type)
            self.editor_window.grab_set()
        else:
            self.editor_window.focus()

    def open_normal_schedule_editor(self):
        """Open the schedule editor for the normal schedule."""
        self._open_schedule_editor(schedule_type="normal")

    def open_alternative_schedule_editor(self):
        """Open the schedule editor for the alternative schedule."""
        self._open_schedule_editor(schedule_type="alternative")

    def open_schedule_config_editor(self):
        """Open the schedule configuration editor window."""
        if self.config_editor_window is None or not self.config_editor_window.winfo_exists():
            self.config_editor_window = ScheduleConfigEditorWindow(self)
            self.config_editor_window.grab_set()
        else:
            self.config_editor_window.focus()

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
        """Handle the closing of the application with a confirmation dialog."""
        # Show a confirmation dialog
        response = self.ask_background_or_exit()
        if response == "background":
            # Hide to system tray
            self.withdraw()  # Hide the window
            self.background_mode = True
        elif response == "exit":
            # Exit the application completely
            if self.service_running:
                self.stop_service()
            if self.editor_window:
                self.editor_window.destroy()
            if self.config_editor_window: # Destroy config editor if open
                self.config_editor_window.destroy()
            if self.songs_window:
                self.songs_window.destroy()
            # Stop the tray icon
            if hasattr(self, 'tray_icon') and self.tray_icon.icon:
                self.tray_icon.icon.stop()
            self.destroy()

    def ask_background_or_exit(self):
        """Show a dialog asking whether to run in background or exit."""
        # Create a temporary dialog window
        dialog = BackgroundDialog(self)
        self.wait_window(dialog)
        return dialog.result

# Background Dialog Class
class BackgroundDialog(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Потвърждение")
        self.geometry("400x150")
        self.resizable(False, False)

        # Center the dialog
        self.transient(parent)
        self.grab_set()

        # Result variable
        self.result = None

        # Create widgets
        label = customtkinter.CTkLabel(self, text="Искате ли приложението да продължи\nработа на заден план?",
                                      font=customtkinter.CTkFont(size=14))
        label.pack(pady=20, padx=20)

        button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=10)

        background_btn = customtkinter.CTkButton(button_frame, text="Заден план",
                                               command=self.background_action,
                                               fg_color="#2CC985",
                                               hover_color="#25A96F")
        background_btn.pack(side="left", padx=10)

        exit_btn = customtkinter.CTkButton(button_frame, text="Изход",
                                          command=self.exit_action,
                                          fg_color="#E84545",
                                          hover_color="#C53636")
        exit_btn.pack(side="left", padx=10)

        # Center the window
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def background_action(self):
        self.result = "background"
        self.destroy()

    def exit_action(self):
        self.result = "exit"
        self.destroy()


# --- Web Panel ---
flask_app = Flask(__name__, template_folder='web_panel/templates', static_folder='web_panel/static')
flask_app.secret_key = 'school_bell_secret_key'  # Needed for sessions






def load_credentials():
    """Load username and password from web_panel_credentials.txt file."""
    credentials_file = 'web_panel_credentials.txt'
    if not os.path.exists(credentials_file):
        # Create default credentials file if it doesn't exist
        with open(credentials_file, 'w', encoding='utf-8') as f:
            f.write("# This file contains the username and password for the web panel.\n")
            f.write("# WARNING: Storing credentials in plain text is INSECURE and not recommended for production environments.\n")
            f.write("#\n")
            f.write("# Format: username:password\n")
            f.write("# Example: admin:password123\n")
            f.write("#\n")
            f.write("# Default credentials:\n")
            f.write("admin:admin123\n")
        return {"username": "admin", "password": "admin123"}

    with open(credentials_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # Split on the first colon only, in case password contains colons
            parts = line.split(':', 1)
            if len(parts) == 2:
                username = parts[0].strip()
                password = parts[1].strip()
                return {"username": username, "password": password}

    # If no valid credentials found, return defaults
    return {"username": "admin", "password": "admin123"}

def authenticate_user(username, password):
    """Check if the provided username and password match the stored credentials."""
    credentials = load_credentials()
    return username == credentials["username"] and password == credentials["password"]

def login_required(f):
    """Decorator to require login for certain routes using HTTP Basic Auth."""
    from functools import wraps
    # No need for base64 import if request.authorization handles decoding

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or not authenticate_user(auth.username, auth.password):
            return Response(
                'Не може да се удостоверите за този URL.\n'
                'Трябва да влезете с правилни данни.', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'})
        # Store username in session for use in templates
        session['username'] = auth.username
        return f(*args, **kwargs)
    return decorated_function





def get_song_list():
    """Returns a list of available songs."""
    try:
        return [s for s in os.listdir(RESOURCES_DIR) if s.endswith((".mp3", ".wav", ".ogg"))]
    except FileNotFoundError:
        return []

@flask_app.route('/')
@login_required
def index():
    """Main page, displays the schedule."""
    schedule = load_schedule()
    schedule.sort(key=lambda x: (DAYS_OF_WEEK.index(x['day']), x['time']))
    songs = get_song_list()
    return render_template('index.html', schedule=schedule, days_of_week=DAYS_OF_WEEK, songs=songs)

@flask_app.route('/add', methods=['POST'])
@login_required
def add_entry():
    """Adds a new entry to the schedule."""
    day = request.form.get('day')
    time = request.form.get('time')
    song = request.form.get('song')

    if not day or not time or not song:
        return jsonify({'status': 'error', 'message': 'Моля, попълнете всички полета.'}), 400

    try:
        hour, minute = map(int, time.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Invalid time range")
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Невалиден формат за час. Моля, използвайте HH:MM.'}), 400

    schedule = load_schedule()
    if any(entry['day'] == day and entry['time'] == time for entry in schedule):
        return jsonify({'status': 'warning', 'message': 'Такъв запис вече съществува.'}), 409 # Conflict

    schedule.append({'day': day, 'time': time, 'song': song if song != "Случайна" else None})
    save_schedule(schedule)
    return jsonify({'status': 'success', 'message': 'Записът е добавен успешно.'}), 201 # Created
@flask_app.route('/delete', methods=['POST'])
@login_required
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
@login_required
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
@login_required
def stop_sound_web():
    """Stops any currently playing music."""
    try:
        mixer.music.stop()
        log_message(shared_state.gui_app, "[WEB] Музиката е спряна ръчно.")
        return jsonify({'status': 'success', 'message': 'Музиката е спряна.'})
    except Exception as e:
        log_message(shared_state.gui_app, f"[WEB-ERROR] Грешка при спиране на музика: {e}")
        return jsonify({'status': 'error', 'message': f"Грешка при спиране на музиката: {e}"}), 500

@flask_app.route('/set-volume', methods=['POST'])
@login_required
def set_volume_web():
    """Sets the volume from the web panel."""
    volume = request.form.get('volume')
    if volume is None:
        return jsonify({'status': 'error', 'message': 'Missing volume parameter'}), 400

    try:
        volume_float = float(volume)
        if not (0.0 <= volume_float <= 1.0):
            raise ValueError("Volume must be between 0.0 and 1.0")

        if shared_state.gui_app:
            # Use after() to ensure thread safety with tkinter
            shared_state.gui_app.after(0, shared_state.gui_app.set_volume, volume_float)
            # Also update the GUI slider directly to keep it synchronized
            shared_state.gui_app.after(0, shared_state.gui_app.volume_slider.set, volume_float)
            log_message(shared_state.gui_app, f"[WEB] Силата на звука е настроена на {int(volume_float * 100)}%")
            return jsonify({'status': 'success', 'message': f'Volume set to {volume_float}'})
        else:
            return jsonify({'status': 'error', 'message': 'GUI app not found'}), 500

    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Invalid volume format'}), 400

@flask_app.route('/toggle-service', methods=['POST'])
@login_required
def toggle_service_web():
    """Toggles the scheduler service from the web panel."""
    if shared_state.gui_app:
        shared_state.gui_app.toggle_service()
        return jsonify({'status': 'success', 'service_running': shared_state.gui_app.service_running})
    return jsonify({'status': 'error', 'message': 'GUI app not found'}), 500

@flask_app.route('/toggle-quiet-mode', methods=['POST'])
@login_required
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
@login_required
def status():
    """Returns the current status of the service."""
    if shared_state.gui_app:
        return jsonify({
            'service_running': shared_state.gui_app.service_running,
            'quiet_mode': shared_state.gui_app.quiet_mode.get(),
            'volume': mixer.music.get_volume()
        })
    return jsonify({'service_running': False, 'quiet_mode': False, 'volume': 1.0})

@flask_app.route('/keep-alive')
@login_required
def keep_alive():
    """Keeps the session alive by refreshing it."""
    # This endpoint just refreshes the session
    session.modified = True
    return jsonify({'status': 'ok'})


@flask_app.route('/stream-logs')
@login_required
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
@login_required
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

@flask_app.route('/login')
def login():
    """Login route - since we're using HTTP Basic Auth, this just triggers the auth dialog."""
    # This route will trigger the basic auth dialog by returning 401
    # The actual authentication happens in the login_required decorator
    return Response(
        'Моля влезте с вашите данни.',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

@flask_app.route('/logout')
def logout():
    """Logout route that prompts the browser to clear authentication credentials."""
    # Return a 401 Unauthorized response to clear the basic auth credentials
    return Response(
        'Вие бяхте отписани от системата.',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

    
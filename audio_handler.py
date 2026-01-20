"""
Audio handling functions for the School Bell application.
"""
import os
import random
import schedule
from pygame import mixer
from config import RESOURCES_DIR
from visual_notification import show_visual_bell_notification


def set_volume(volume):
    """Set the volume of the audio player."""
    mixer.music.set_volume(float(volume))
    # Note: This function is called from the main app to update the volume percentage label
    # The volume percentage calculation happens in the main app


def play_song(app, song_name=None):
    """Play a song for scheduled bells with a fallback to default.mp3."""
    if app.quiet_mode.get():
        show_visual_bell_notification(app)
        return schedule.CancelJob

    app.log_message("Време е за звънец! Търсене на песен...")
    show_visual_bell_notification(app)

    # --- Nested helper function for playing sound ---
    def attempt_play(song_filename, is_fallback=False):
        try:
            # Check if the song file exists
            local_path = os.path.join(RESOURCES_DIR, song_filename)
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Файлът '{song_filename}' не е намерен в '{RESOURCES_DIR}'.")

            # Try to load and play
            app.log_message(f"Зареждане на '{song_filename}'...")
            mixer.music.load(local_path)
            mixer.music.play()
            app.log_message(f"Успешно пусната: '{song_filename}'.")
            return True  # Indicate success

        except Exception as e:
            error_prefix = "[FALLBACK ERROR]" if is_fallback else "[SONG ERROR]"
            app.log_message(f"{error_prefix} Неуспешно пускане на '{song_filename}': {e}")
            return False # Indicate failure

    # --- Main song selection and play logic ---
    try:
        song_list = [s for s in os.listdir(RESOURCES_DIR) if s.endswith((".mp3", ".wav", ".ogg"))]
        if not song_list:
            app.log_message(f"[ГРЕШКА] Няма песни в директория '{RESOURCES_DIR}'.")
            return schedule.CancelJob

        # Determine the INTENDED song to play
        intended_song_filename = None
        if song_name: # A specific song name was provided
            intended_song_filename = song_name
        else: # No specific song name provided (e.g., "Случайна" in schedule)
            intended_song_filename = random.choice(song_list)
            app.log_message(f"Няма зададена песен в графика, избрана е случайна: '{intended_song_filename}'.")

        # Attempt to play the determined first song
        if not attempt_play(intended_song_filename):
            # If the first attempt fails (e.g., file not found, corrupt), try the fallback
            app.log_message(f"Първият опит за пускане на '{intended_song_filename}' се провали. Опитвам резервна песен 'default.mp3'...")
            if not attempt_play('default.mp3', is_fallback=True):
                 app.log_message(f"[CRITICAL] Неуспешно пускане и на резервната песен 'default.mp3'.")

    except Exception as e:
        app.log_message(f"[FATAL] Критична грешка в audio_handler: {e}")
        # As a last resort, try to play the fallback even if song selection fails
        attempt_play('default.mp3', is_fallback=True)

    return schedule.CancelJob


def play_song_manual(app, song_name=None):
    """Play a song for manual bells with stopping capability."""
    app.log_message("Време е за звънец! Търсене на песен...")

    # Show visual notification
    show_visual_bell_notification(app)

    try:
        song_list = [s for s in os.listdir(RESOURCES_DIR) if s.endswith((".mp3", ".wav", ".ogg"))]
        if not song_list:
            app.log_message(f"[ГРЕШКА] Няма песни в '{RESOURCES_DIR}'.")
            return

        song_to_play = None
        if song_name and song_name in song_list:
            song_to_play = song_name
        else:
            song_to_play = random.choice(song_list)

        local_path = os.path.join(RESOURCES_DIR, song_to_play)

        app.log_message(f"Пускане на '{song_to_play}'...")
        mixer.music.load(local_path)
        mixer.music.play()

        # Wait for the music to finish or be stopped manually
        while mixer.music.get_busy():
            import time
            time.sleep(0.5)
            # Check if the button text has changed back to "Пусни звънеца сега" indicating stop was requested
            if app.manual_ring_button.cget("text") == "Пусни звънеца сега":
                break

    except Exception as e:
        app.log_message(f"[ГРЕШКА] Проблем при пускане на песен: {e}")
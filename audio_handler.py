"""
Audio handling functions for the School Bell application.
"""
import os
import random
from pygame import mixer
from config import RESOURCES_DIR
from visual_notification import show_visual_bell_notification


def set_volume(volume):
    """Set the volume of the audio player."""
    mixer.music.set_volume(float(volume))
    # Note: This function is called from the main app to update the volume percentage label
    # The volume percentage calculation happens in the main app


def play_song(app, song_name=None):
    """Play a song for scheduled bells."""
    if app.quiet_mode.get():
        # Still show visual notification even in quiet mode
        show_visual_bell_notification(app)
        return "CANCEL_JOB"

    app.log_message("Време е за звънец! Търсене на песен...")

    # Show visual notification
    show_visual_bell_notification(app)

    try:
        song_list = [s for s in os.listdir(RESOURCES_DIR) if s.endswith((".mp3", ".wav", ".ogg"))]
        if not song_list:
            app.log_message(f"[ГРЕШКА] Няма песни в '{RESOURCES_DIR}'.")
            return "CANCEL_JOB"

        song_to_play = None
        if song_name and song_name in song_list:
            song_to_play = song_name
        else:
            song_to_play = random.choice(song_list)

        local_path = os.path.join(RESOURCES_DIR, song_to_play)

        app.log_message(f"Пускане на '{song_to_play}'...")
        mixer.music.load(local_path)
        mixer.music.play()

    except Exception as e:
        app.log_message(f"[ГРЕШКА] Проблем при пускане на песен: {e}")
    return "CANCEL_JOB"


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
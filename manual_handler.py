"""
Manual bell handling functions for the School Bell application.
"""
import threading
import customtkinter
from pygame import mixer
from utils import log_message


def manual_ring(app):
    """Handle manual bell ringing with toggle functionality."""
    if app.quiet_mode.get():
        log_message(app, "Ръчното пускане е спряно (Тих режим).")
        return
        
    # Check if currently playing by looking at button text
    if app.manual_ring_button.cget("text") == "Спри звънеца":
        # Music is currently playing, so stop it
        if mixer.music.get_busy():
            mixer.music.stop()
        log_message(app, "Ръчното пускане е спряно.")
        _reset_manual_ring_button(app)
    else:
        # Start new playback
        app.manual_ring_button.configure(text="Спри звънеца", fg_color="#E84545")
        log_message(app, "Ръчно пускане на звънеца...")
        
        # Get selected song from dropdown
        selected_song = app.manual_song_var.get()
        if selected_song == "Случайна":
            selected_song = None
            
        app.manual_ring_playing_thread = threading.Thread(
            target=app._play_manual_bell, 
            args=(selected_song,), 
            daemon=True
        )
        app.manual_ring_playing_thread.start()
        app.after(100, _check_manual_ring_thread, app)


def _check_manual_ring_thread(app):
    """Check if the manual ring thread is still running."""
    if app.manual_ring_playing_thread and app.manual_ring_playing_thread.is_alive():
        app.after(100, _check_manual_ring_thread, app)
    else:
        # Thread is no longer alive, ensure button is reset if needed
        if app.manual_ring_button.cget("text") == "Спри звънеца": # Only reset if still showing playing status
            _reset_manual_ring_button(app)


def _reset_manual_ring_button(app):
    """Reset the manual ring button to its original state."""
    # Reset to default color using theme manager
    app.manual_ring_button.configure(
        text="Пусни звънеца сега",
        fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"]
    )
    app.manual_ring_playing_thread = None
    log_message(app, "Ръчен звънец приключи.")
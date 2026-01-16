"""
Test script to check imports and basic functionality
"""
import sys
print("Starting import test...", flush=True)

try:
    print("Testing imports...", flush=True)

    import customtkinter
    print("✓ customtkinter imported successfully", flush=True)

    import threading
    print("✓ threading imported successfully", flush=True)

    import schedule
    print("✓ schedule imported successfully", flush=True)

    import time
    print("✓ time imported successfully", flush=True)

    from tkinter import *
    print("✓ tkinter imported successfully", flush=True)

    import os
    print("✓ os imported successfully", flush=True)

    from pygame import mixer
    print("✓ pygame.mixer imported successfully", flush=True)

    from datetime import datetime
    print("✓ datetime imported successfully", flush=True)

    # Test config import
    from config import APP_NAME, WIDTH, HEIGHT, RESOURCES_DIR, SCHEDULE_FILE
    print(f"✓ Config imported successfully: {APP_NAME}", flush=True)

    # Test other imports
    from utils import load_schedule, save_schedule, log_message
    print("✓ Utils imported successfully", flush=True)

    from ui_components import setup_left_panel, setup_center_panel, setup_right_panel
    print("✓ UI Components imported successfully", flush=True)

    from audio_handler import set_volume, play_song, play_song_manual
    print("✓ Audio Handler imported successfully", flush=True)

    from scheduler import start_service, stop_service, run_scheduler, update_next_bell_label
    print("✓ Scheduler imported successfully", flush=True)

    from manual_handler import manual_ring
    print("✓ Manual Handler imported successfully", flush=True)

    from schedule_editor import ScheduleEditorWindow
    print("✓ Schedule Editor imported successfully", flush=True)

    print("\nAll imports successful!", flush=True)

except ImportError as e:
    print(f"Import error: {e}", flush=True)
    import traceback
    print(traceback.format_exc(), flush=True)
except Exception as e:
    print(f"Other error: {e}", flush=True)
    import traceback
    print(traceback.format_exc(), flush=True)
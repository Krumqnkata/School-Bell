"""
Scheduler functions for the School Bell application.
"""
import schedule
import time
import threading
from config import DAY_MAP_BG_TO_EN
from utils import log_message


def start_service(app):
    """Start the bell scheduling service."""
    app.service_running = True
    log_message(app, "Услугата стартира...")
    app.status_label.configure(text="РАБОТИ", text_color="#2CC985")
    app.start_stop_button.configure(text="СТОП")
    app.edit_button.configure(state="disabled")
    app.scheduler_thread = threading.Thread(target=run_scheduler, args=(app,), daemon=True)
    app.scheduler_thread.start()


def stop_service(app):
    """Stop the bell scheduling service."""
    app.service_running = False
    schedule.clear()
    from pygame import mixer
    if mixer.music.get_busy(): 
        mixer.music.stop()
    app.status_label.configure(text="СПРЯН", text_color="#E84545")
    app.start_stop_button.configure(text="СТАРТ")
    app.next_bell_label.configure(text="--:--:--")
    app.edit_button.configure(state="normal")
    log_message(app, "Услугата е спряна.")


def run_scheduler(app):
    """Run the scheduler loop."""
    log_message(app, "Планиране на задачите...")
    schedule.clear()
    for job in app.bell_times:
        day_en = DAY_MAP_BG_TO_EN.get(job['day'])
        if day_en:
            try:
                getattr(schedule.every(), day_en).at(job['time']).do(lambda song_name=job.get('song'): app.play_song(song_name=song_name))
            except Exception as e:
                log_message(app, f"[ГРЕШКА] Невалидна задача: {job['day']} в {job['time']}. Грешка: {e}")

    log_message(app, "Всички задачи са планирани.")

    while app.service_running:
        schedule.run_pending()
        time.sleep(1)


def update_next_bell_label(app):
    """Update the next bell label."""
    if app.service_running:
        if schedule.jobs:
            next_run_val = schedule.next_run()
            if next_run_val:
                from config import BG_WEEKDAYS
                from datetime import datetime
                day_text = BG_WEEKDAYS[next_run_val.weekday()]
                app.next_bell_label.configure(text=f"{day_text} в {next_run_val.strftime('%H:%M:%S')}")
            else:
                app.next_bell_label.configure(text="Няма предстоящи")
        else:
            app.next_bell_label.configure(text="Няма планирани")
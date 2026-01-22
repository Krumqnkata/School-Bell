"""
Scheduler functions for the School Bell application.
"""
import schedule
import time
import threading
from datetime import timedelta
from config import DAY_MAP_BG_TO_EN
from utils import log_message


def start_service(app):
    """Start the bell scheduling service."""
    app.service_running = True
    log_message(app, "Услугата стартира...")
    app.status_label.configure(text="РАБОТИ", text_color="#2CC985")
    app.start_stop_button.configure(text="СТОП")
    app.open_schedule_config_button.configure(state="disabled")
    app.open_normal_schedule_editor_button.configure(state="disabled")
    app.open_alternative_schedule_editor_button.configure(state="disabled")
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
    app.open_schedule_config_button.configure(state="normal")
    app.open_normal_schedule_editor_button.configure(state="normal")
    app.open_alternative_schedule_editor_button.configure(state="normal")
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
        from datetime import datetime
        from config import DAY_MAP_BG_TO_EN, BG_WEEKDAYS
        import calendar

        now = datetime.now()
        current_time = now.time()
        current_weekday = now.weekday()
        current_day_bg = BG_WEEKDAYS[current_weekday]

        # Find the next scheduled bell
        next_bell = None
        min_diff = float('inf')

        # Check all scheduled times
        for entry in app.bell_times:
            day_bg = entry['day']
            time_str = entry['time']

            # Parse the time
            try:
                bell_time = datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                continue

            # Calculate the difference in days and time
            day_index = BG_WEEKDAYS.index(day_bg)

            if day_index == current_weekday:
                # Same day - check if time has passed
                if bell_time > current_time:
                    # Today's bell hasn't happened yet
                    diff_seconds = (datetime.combine(now.date(), bell_time) - now).total_seconds()
                    if 0 < diff_seconds < min_diff:
                        min_diff = diff_seconds
                        next_bell = (day_bg, time_str)
            elif day_index > current_weekday:
                # Future day in this week
                days_ahead = day_index - current_weekday
                temp_date = now + timedelta(days=days_ahead)
                temp_datetime = datetime.combine(temp_date.date(), bell_time)
                diff_seconds = (temp_datetime - now).total_seconds()
                if diff_seconds < min_diff:
                    min_diff = diff_seconds
                    next_bell = (day_bg, time_str)
            else:
                # Day in next week
                days_ahead = 7 - current_weekday + day_index
                temp_date = now + timedelta(days=days_ahead)
                temp_datetime = datetime.combine(temp_date.date(), bell_time)
                diff_seconds = (temp_datetime - now).total_seconds()
                if diff_seconds < min_diff:
                    min_diff = diff_seconds
                    next_bell = (day_bg, time_str)

        if next_bell:
            day, time_str = next_bell
            app.next_bell_label.configure(text=f"{day} в {time_str}")
        else:
            app.next_bell_label.configure(text="Няма предстоящи")
    else:
        app.next_bell_label.configure(text="--:--:--")
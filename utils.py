"""
Utility functions for the School Bell application.
"""
import csv
import os
from datetime import datetime
from tkinter import END
from config import NORMAL_SCHEDULE_FILE, ALTERNATIVE_SCHEDULE_FILE, SCHEDULE_CONFIG_FILE, BG_WEEKDAYS
import shared_state


def load_schedule_config():
    """Load the schedule configuration from schedule_config.txt."""
    schedule_config = {}
    try:
        with open(SCHEDULE_CONFIG_FILE, mode='r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    day, schedule_type = line.split('=', 1)
                    schedule_config[day.strip()] = schedule_type.strip()
    except FileNotFoundError:
        print(f"[LOG] [ИНФО] {SCHEDULE_CONFIG_FILE} не е намерен, създавам нов с настройки по подразбиране.")
        # Create default config if file not found
        default_config = {day: "normal" for day in BG_WEEKDAYS}
        save_schedule_config(default_config)
        return default_config
    except Exception as e:
        print(f"[LOG] [ГРЕШКА] при зареждане на {SCHEDULE_CONFIG_FILE}: {e}")
    return schedule_config

def save_schedule_config(schedule_config):
    """Save the schedule configuration to schedule_config.txt."""
    try:
        with open(SCHEDULE_CONFIG_FILE, mode='w', encoding='utf-8') as file:
            for day, schedule_type in schedule_config.items():
                file.write(f"{day}={schedule_type}\n")
    except Exception as e:
        print(f"[LOG] [ГРЕШКА] при запазване на {SCHEDULE_CONFIG_FILE}: {e}")


def _read_schedule_file(filepath):
    """Helper function to read a single CSV schedule file."""
    schedule_data = []
    try:
        with open(filepath, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            for row in reader:
                entry = {'day': row['Ден'], 'time': row['Час']}
                if 'Песен' in fieldnames:
                    entry['song'] = row.get('Песен') if row.get('Песен') else None
                else:
                    entry['song'] = None
                schedule_data.append(entry)
    except FileNotFoundError:
        print(f"[LOG] [ИНФО] {filepath} не е намерен.")
    except Exception as e:
        print(f"[LOG] [ГРЕШКА] при зареждане на {filepath}: {e}")
    return schedule_data


def load_schedule():
    """Load the combined bell schedule based on the configuration."""
    schedule_config = load_schedule_config()
    normal_schedule = _read_schedule_file(NORMAL_SCHEDULE_FILE)
    alternative_schedule = _read_schedule_file(ALTERNATIVE_SCHEDULE_FILE)

    combined_schedule_data = []

    # Build a dictionary for faster lookup by day
    normal_by_day = {day: [] for day in BG_WEEKDAYS}
    for entry in normal_schedule:
        normal_by_day[entry['day']].append(entry)

    alternative_by_day = {day: [] for day in BG_WEEKDAYS}
    for entry in alternative_schedule:
        alternative_by_day[entry['day']].append(entry)

    for day in BG_WEEKDAYS:
        schedule_type = schedule_config.get(day, "normal") # Default to normal
        if schedule_type == "normal":
            combined_schedule_data.extend(normal_by_day[day])
        elif schedule_type == "alternative":
            combined_schedule_data.extend(alternative_by_day[day])
    
    return combined_schedule_data





def save_specific_schedule(filepath, schedule_data):
    """Save the provided schedule data to a specific CSV file."""
    try:
        with open(filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['Ден', 'Час', 'Песен'])
            writer.writeheader()
            writer.writerows([{'Ден': r['day'], 'Час': r['time'], 'Песен': r.get('song')} for r in schedule_data])
        print(f"[LOG] [ИНФО] Графикът е запазен във {filepath}.")
    except Exception as e:
        print(f"[LOG] [ГРЕШКА] при запазване на {filepath}: {e}")


def save_schedule(schedule_data):
    """Save the bell schedule to the appropriate CSV files based on configuration."""
    schedule_config = load_schedule_config()

    normal_schedule_to_save = []
    alternative_schedule_to_save = []

    # Separate schedule entries based on the current config
    for entry in schedule_data:
        day = entry['day']
        schedule_type = schedule_config.get(day, "normal") # Default to normal
        if schedule_type == "normal":
            normal_schedule_to_save.append(entry)
        elif schedule_type == "alternative":
            alternative_schedule_to_save.append(entry)

    # Helper to write to a specific CSV file
    def _write_schedule_file(filepath, data):
        try:
            with open(filepath, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['Ден', 'Час', 'Песен'])
                writer.writeheader()
                writer.writerows([{'Ден': r['day'], 'Час': r['time'], 'Песен': r.get('song')} for r in data])
        except Exception as e:
            print(f"[LOG] [ГРЕШКА] при запазване на {filepath}: {e}")
    
    _write_schedule_file(NORMAL_SCHEDULE_FILE, normal_schedule_to_save)
    _write_schedule_file(ALTERNATIVE_SCHEDULE_FILE, alternative_schedule_to_save)


def log_message(app, msg):
    """Log a message to the application's log box and the shared queue."""
    now = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{now}] {msg}"
    
    # Put the message in the queue for the web panel
    shared_state.log_queue.put(log_entry)

    # If the GUI app is running, also log to its text box
    if app and hasattr(app, 'log_box'):
        app.log_box.config(state="normal")
        app.log_box.insert(END, f"[{now}] ", 'timestamp')
        app.log_box.insert(END, f"{msg}\n", 'message')
        app.log_box.config(state="disabled")
        app.log_box.see(END)
    else:
        # Fallback for non-GUI logging
        print(log_entry)
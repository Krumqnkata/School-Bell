"""
Utility functions for the School Bell application.
"""
import csv
import os
from datetime import datetime
from tkinter import END
from config import SCHEDULE_FILE
import shared_state


def load_schedule():
    """Load the bell schedule from the CSV file."""
    schedule_data = []
    try:
        with open(SCHEDULE_FILE, mode='r', newline='', encoding='utf-8') as file:
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
        print(f"[LOG] [ИНФО] {SCHEDULE_FILE} не е намерен, създавам нов.")
        save_schedule([])
    except Exception as e:
        print(f"[LOG] [ГРЕШКА] при зареждане на {SCHEDULE_FILE}: {e}")
    return schedule_data


def save_schedule(schedule_data):
    """Save the bell schedule to the CSV file."""
    try:
        with open(SCHEDULE_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['Ден', 'Час', 'Песен'])
            writer.writeheader()
            writer.writerows([{'Ден': r['day'], 'Час': r['time'], 'Песен': r.get('song')} for r in schedule_data])
    except Exception as e:
        print(f"[LOG] [ГРЕШКА] при запазване на {SCHEDULE_FILE}: {e}")


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
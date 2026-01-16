"""
Configuration constants for the School Bell application.
"""

# --- App Conf ---
APP_NAME = "Училищен Звънец v2.5/БЕТА/"
WIDTH = 1100
HEIGHT = 700
RESOURCES_DIR = "songs"
SCHEDULE_FILE = "schedule.csv"

# --- Colors ---
GREEN = "#2CC985"
RED = "#E84545"
BLUE = "#3a7ebf"

# --- Day Mapping ---
DAY_MAP_BG_TO_EN = {
    "Понеделник": "monday", "Вторник": "tuesday", "Сряда": "wednesday",
    "Четвъртък": "thursday", "Петък": "friday", "Събота": "saturday", "Неделя": "sunday",
}
DAYS_OF_WEEK = list(DAY_MAP_BG_TO_EN.keys())
BG_WEEKDAYS = ["Понеделник", "Вторник", "Сряда", "Четвъртък", "Петък", "Събота", "Неделя"]
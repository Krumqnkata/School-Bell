# This module holds a reference to the main GUI application instance
# and a shared queue for log messages to allow other parts of the program 
# (like the Flask web panel) to interact with it.
import queue

gui_app = None
log_queue = queue.Queue()

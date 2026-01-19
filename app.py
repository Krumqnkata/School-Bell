"""
Main application file for the School Bell application.
"""
from main import SchoolBellApp
import shared_state

if __name__ == "__main__":
    app = SchoolBellApp()
    shared_state.gui_app = app
    app.mainloop()
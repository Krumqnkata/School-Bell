import customtkinter
from config import BG_WEEKDAYS
from utils import load_schedule_config, save_schedule_config, log_message

class ScheduleConfigEditorWindow(customtkinter.CTkToplevel):
    def __init__(self, parent_app):
        super().__init__(parent_app)
        self.parent_app = parent_app
        self.title("Настройки на графика")
        self.geometry("400x500")
        self.resizable(False, False)

        self.grab_set() # Make window modal
        self.protocol("WM_DELETE_WINDOW", self.cancel_config) # Handle closing via X button

        self.current_schedule_config = load_schedule_config()
        self.day_schedule_vars = {} # To store StringVar for each day

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Labels and OptionMenus for each day
        customtkinter.CTkLabel(self, text="Изберете тип график за всеки ден:", font=customtkinter.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 20), sticky="ew")

        for i, day in enumerate(BG_WEEKDAYS):
            customtkinter.CTkLabel(self, text=day, font=customtkinter.CTkFont(size=14)).grid(row=i+1, column=0, padx=20, pady=5, sticky="w")
            
            day_var = customtkinter.StringVar(value=self.current_schedule_config.get(day, "normal"))
            self.day_schedule_vars[day] = day_var
            
            option_menu = customtkinter.CTkOptionMenu(self, variable=day_var, values=["normal", "alternative"])
            option_menu.grid(row=i+1, column=1, padx=20, pady=5, sticky="ew")

        # Buttons
        button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=len(BG_WEEKDAYS)+1, column=0, columnspan=2, pady=20)
        
        save_button = customtkinter.CTkButton(button_frame, text="Запази", command=self.save_config)
        save_button.pack(side="left", padx=10)

        cancel_button = customtkinter.CTkButton(button_frame, text="Откажи", command=self.cancel_config)
        cancel_button.pack(side="left", padx=10)

    def save_config(self):
        """Save the updated schedule configuration."""
        new_config = {day: var.get() for day, var in self.day_schedule_vars.items()}
        save_schedule_config(new_config)
        log_message(self.parent_app, "Конфигурацията на дневния график е обновена.")
        self.parent_app.reload_schedule_from_csv() # Trigger reload in main app
        self.destroy()

    def cancel_config(self):
        """Discard changes and close the window."""
        self.destroy()

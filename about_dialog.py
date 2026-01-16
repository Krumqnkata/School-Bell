"""
About dialog for the School Bell application.
"""
import customtkinter


class AboutDialog(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Относно")
        self.geometry("400x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Center the window
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (300 // 2)
        self.geometry(f"+{x}+{y}")
        
        # Create the content
        frame = customtkinter.CTkFrame(self)
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        title_label = customtkinter.CTkLabel(
            frame, 
            text="Училищен Звънец", 
            font=customtkinter.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        version_label = customtkinter.CTkLabel(
            frame, 
            text="Версия BETA 2.5", 
            font=customtkinter.CTkFont(size=14)
        )
        version_label.pack(pady=5)
        
        authors_label = customtkinter.CTkLabel(
            frame, 
            text="Автори:", 
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        authors_label.pack(pady=(20, 5))
        
        # Replace with actual author names
        authors_text = customtkinter.CTkLabel(
            frame, 
            text="Разработено от:\n\nКрум Крумов и Александър Димитров", 
            font=customtkinter.CTkFont(size=14),
            justify="center"
        )
        authors_text.pack(pady=10)
        
        description_label = customtkinter.CTkLabel(
            frame, 
            text="Програма за автоматично пускане на звънци в училище", 
            font=customtkinter.CTkFont(size=12),
            wraplength=350
        )
        description_label.pack(pady=10)
        
        close_button = customtkinter.CTkButton(
            frame, 
            text="Затвори", 
            command=self.destroy
        )
        close_button.pack(pady=(20, 20))
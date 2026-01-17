"""
Visual notification system for the School Bell application.
"""
import customtkinter
from datetime import datetime


class VisualNotification:
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.notification_window = None
        
    def show_visual_notification(self, message="Време е за звънец!", duration=5000):
        """
        Show a visual notification window.
        
        Args:
            message (str): The message to display
            duration (int): Duration in milliseconds before auto-closing
        """
        # Close any existing notification
        if self.notification_window and self.notification_window.winfo_exists():
            self.notification_window.destroy()
            
        # Create a new notification window
        self.notification_window = customtkinter.CTkToplevel(self.parent_app)
        self.notification_window.title("Училищен Звънец - Уведомление")
        self.notification_window.geometry("400x200")
        self.notification_window.resizable(False, False)
        
        # Remove window decorations to make it more prominent
        self.notification_window.overrideredirect(True)
        
        # Position the window in the center of the screen
        self.center_window()
        
        # Set window attributes to stay on top
        self.notification_window.attributes("-topmost", True)
        
        # Bind click event to close the notification
        self.notification_window.bind("<Button-1>", lambda e: self.close_notification())
        
        # Create the content
        main_frame = customtkinter.CTkFrame(self.notification_window, fg_color="#2CC985")
        main_frame.pack(expand=True, fill="both", padx=2, pady=2)
        
        # Add the message
        label = customtkinter.CTkLabel(
            main_frame, 
            text=message,
            font=customtkinter.CTkFont(size=24, weight="bold"),
            text_color="white"
        )
        label.pack(expand=True, pady=20, padx=20)
        
        # Add time indicator
        time_label = customtkinter.CTkLabel(
            main_frame,
            text=datetime.now().strftime("%H:%M:%S"),
            font=customtkinter.CTkFont(size=14),
            text_color="white"
        )
        time_label.pack(side="bottom", pady=(0, 10))
        
        # Schedule automatic closing
        self.notification_window.after(duration, self.close_notification)
        
        # Bring to front periodically to ensure it stays visible
        self.bring_to_front()
    
    def center_window(self):
        """Center the notification window on screen."""
        self.notification_window.update_idletasks()
        
        # Get screen dimensions
        screen_width = self.notification_window.winfo_screenwidth()
        screen_height = self.notification_window.winfo_screenheight()
        
        # Get window dimensions
        window_width = 400
        window_height = 200
        
        # Calculate position
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        # Apply geometry
        self.notification_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def bring_to_front(self):
        """Bring the notification to the front periodically."""
        if self.notification_window and self.notification_window.winfo_exists():
            self.notification_window.lift()
            self.notification_window.attributes("-topmost", True)
            # Repeat every 2 seconds to maintain topmost status
            self.notification_window.after(2000, self.bring_to_front)
    
    def close_notification(self):
        """Close the notification window."""
        if self.notification_window and self.notification_window.winfo_exists():
            self.notification_window.destroy()
            self.notification_window = None


def show_visual_bell_notification(app):
    """
    Function to show a visual bell notification.
    
    Args:
        app: The main application instance
    """
    if not hasattr(app, 'visual_notifier'):
        app.visual_notifier = VisualNotification(app)
    
    app.visual_notifier.show_visual_notification(message="🔔 Време е за звънец! 🔔")
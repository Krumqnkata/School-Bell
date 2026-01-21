"""
System tray icon implementation for the School Bell application.
"""
import pystray
from PIL import Image, ImageDraw
import threading


class TrayIcon:
    def __init__(self, app):
        self.app = app
        self.icon = None
        self.menu_items = [
            pystray.MenuItem("Покажи приложение", self.show_app, default=True),
            pystray.MenuItem("Скрий приложение", self.hide_app),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Изход", self.quit_app)
        ]
        
        # Create a simple icon
        self.create_icon_image()
        
    def create_icon_image(self):
        """Create a simple icon image for the system tray."""
        # Create a simple image for the tray icon
        image = Image.new('RGB', (64, 64), color=(70, 130, 180))  # Steel blue
        draw = ImageDraw.Draw(image)
        
        # Draw a simple bell shape
        # Outer bell
        draw.ellipse((15, 10, 49, 44), fill=(255, 215, 0))  # Gold
        # Inner bell
        draw.ellipse((20, 15, 44, 39), fill=(70, 130, 180))  # Steel blue
        
        # Handle
        draw.rectangle((29, 5, 35, 15), fill=(105, 105, 105))  # Dim gray
        
        self.image = image

    def show_app(self, icon, item):
        """Show the main application window."""
        self.app.after(0, self._show_app)

    def _show_app(self):
        """Internal method to show the app on the main thread."""
        self.app.deiconify()  # Show the window
        self.app.lift()       # Bring to front
        self.app.focus_force() # Force focus
        self.app.background_mode = False  # Reset background mode flag

    def hide_app(self, icon, item):
        """Hide the main application window to system tray."""
        self.app.after(0, self._hide_app)

    def _hide_app(self):
        """Internal method to hide the app on the main thread."""
        self.app.withdraw()  # Hide the window
        self.app.background_mode = True  # Set background mode flag

    def quit_app(self, icon, item):
        """Quit the application completely."""
        self.app.after(0, self._quit_app)

    def _quit_app(self):
        """Internal method to quit the app on the main thread."""
        # Stop the scheduler if running
        if self.app.service_running:
            self.app.stop_service()
            
        # Destroy the tray icon
        if self.icon:
            self.icon.stop()
            
        # Destroy the main application window
        self.app.destroy()

    def run_icon(self):
        """Run the system tray icon."""
        self.icon = pystray.Icon("School Bell", self.image, "Училищен Звънец", self.menu_items)
        self.icon.run()

    def start_tray_icon(self):
        """Start the system tray icon in a separate thread."""
        tray_thread = threading.Thread(target=self.run_icon, daemon=True)
        tray_thread.start()

    def stop_icon(self):
        """Stop the system tray icon."""
        if self.icon:
            self.icon.stop()
import sys
import os
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
import pystray
from PIL import Image, ImageDraw
import subprocess
import json
from pathlib import Path

class SysWatchTray:
    def __init__(self):
        self.config_file = Path(__file__).parent / "tray_config.json"
        self.load_config()
        self.create_icon()
        
    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.server_url = config.get('server_url', 'ws://localhost:3000')
            else:
                self.server_url = 'ws://localhost:3000'
        except:
            self.server_url = 'ws://localhost:3000'
    
    def save_config(self):
        try:
            config = {'server_url': self.server_url}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def create_icon(self):
        # Create a simple icon
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill='white')
        draw.text((20, 25), "SW", fill='blue')
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem("SysWatch Agent", self.show_about, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Change Server", self.change_server),
            pystray.MenuItem("Restart Service", self.restart_service),
            pystray.MenuItem("View Logs", self.view_logs),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("About", self.show_about),
            pystray.MenuItem("Exit", self.quit_app)
        )
        
        self.icon = pystray.Icon("SysWatch", image, "SysWatch Agent", menu)
    
    def change_server(self, icon, item):
        def show_dialog():
            root = tk.Tk()
            root.withdraw()  # Hide main window
            
            new_url = simpledialog.askstring(
                "Change Server", 
                f"Current server: {self.server_url}\n\nEnter new server URL:",
                initialvalue=self.server_url
            )
            
            if new_url and new_url != self.server_url:
                self.server_url = new_url
                self.save_config()
                
                # Ask to restart service
                if messagebox.askyesno("Restart Required", 
                    "Server URL changed. Restart the SysWatch service to apply changes?"):
                    self.restart_service(None, None)
            
            root.destroy()
        
        threading.Thread(target=show_dialog, daemon=True).start()
    
    def restart_service(self, icon, item):
        def restart():
            try:
                # Stop service
                subprocess.run(['sc', 'stop', 'SysWatch Agent'], 
                             capture_output=True, check=False)
                
                # Wait a moment
                import time
                time.sleep(2)
                
                # Start service
                result = subprocess.run(['sc', 'start', 'SysWatch Agent'], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.show_notification("Service restarted successfully")
                else:
                    self.show_notification(f"Failed to restart service: {result.stderr}")
                    
            except Exception as e:
                self.show_notification(f"Error restarting service: {str(e)}")
        
        threading.Thread(target=restart, daemon=True).start()
    
    def view_logs(self, icon, item):
        def show_logs():
            try:
                # Just open Event Viewer - filtering is too complex
                subprocess.run(['eventvwr.msc'], check=False)
            except Exception as e:
                # Fallback - open Windows Logs folder
                try:
                    subprocess.run(['explorer', 'C:\\Windows\\System32\\winevt\\Logs'], check=False)
                except:
                    self.show_notification(f"Could not open logs: {str(e)}")
        
        threading.Thread(target=show_logs, daemon=True).start()
    
    def show_about(self, icon, item):
        def show_dialog():
            root = tk.Tk()
            root.withdraw()
            
            try:
                version_file = Path(__file__).parent / "version.txt"
                version = version_file.read_text().strip() if version_file.exists() else "Unknown"
            except:
                version = "Unknown"
            
            messagebox.showinfo("About SysWatch Agent", 
                f"SysWatch Agent v{version}\n\n"
                f"Server: {self.server_url}\n"
                f"Status: Running\n\n"
                f"Remote monitoring and management system\n"
                f"© 2025 SysWatch")
            
            root.destroy()
        
        threading.Thread(target=show_dialog, daemon=True).start()
    
    def show_notification(self, message):
        if hasattr(self.icon, 'notify'):
            self.icon.notify(message, "SysWatch Agent")
    
    def quit_app(self, icon, item):
        icon.stop()
        sys.exit(0)
    
    def run(self):
        self.icon.run()

if __name__ == "__main__":
    try:
        app = SysWatchTray()
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Tray application error: {e}")
        sys.exit(1)
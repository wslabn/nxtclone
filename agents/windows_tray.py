import sys
import os
import threading
import subprocess
import json
from pathlib import Path

# Try to import GUI libraries with fallbacks
try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

class SysWatchTray:
    def __init__(self):
        # Use AppData for config to avoid permission issues
        appdata_dir = Path(os.path.expandvars("%APPDATA%")) / "SysWatch"
        appdata_dir.mkdir(exist_ok=True)
        self.config_file = appdata_dir / "tray_config.json"
        self.load_config()
        
        if TRAY_AVAILABLE:
            self.create_icon()
        else:
            print("Tray libraries not available, running in console mode")
            self.run_console_mode()
        
    def load_config(self):
        try:
            detected_url = self.get_agent_server_url()
            if detected_url:
                self.server_url = detected_url
            else:
                if self.config_file.exists():
                    with open(self.config_file, 'r') as f:
                        config = json.load(f)
                        self.server_url = config.get('server_url', 'ws://localhost:3000')
                else:
                    self.server_url = 'ws://localhost:3000'
        except Exception as e:
            self.server_url = 'ws://localhost:3000'
    
    def get_agent_server_url(self):
        try:
            # Try PowerShell method first
            result = subprocess.run(['powershell', '-Command', 
                                   'Get-WmiObject Win32_Process | Where-Object {$_.Name -eq "syswatch-agent-windows.exe"} | Select-Object CommandLine'], 
                                   capture_output=True, text=True)
            
            import re
            match = re.search(r'ws://[^\s"]+', result.stdout)
            if match:
                return match.group(0)
            
            # Fallback to tasklist method
            result = subprocess.run(['wmic', 'process', 'where', 'name="syswatch-agent-windows.exe"', 
                                   'get', 'commandline', '/format:list'], capture_output=True, text=True)
            match = re.search(r'ws://[^\s"]+', result.stdout)
            if match:
                return match.group(0)
            return None
        except:
            return None
    
    def save_config(self):
        try:
            config = {'server_url': self.server_url}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def create_icon(self):
        # Create simple icon
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill='white')
        draw.text((20, 25), "SW", fill='blue')
        
        menu = pystray.Menu(
            pystray.MenuItem("SysWatch Agent", self.show_about, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Change Server", self.change_server),
            pystray.MenuItem("Restart Agent", self.restart_service),
            pystray.MenuItem("Update Agent", self.update_agent),
            pystray.MenuItem("View Status", self.view_status),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.quit_app)
        )
        
        self.icon = pystray.Icon("SysWatch", image, "SysWatch Agent", menu)
    
    def change_server(self, icon, item):
        if not GUI_AVAILABLE:
            return
            
        def show_dialog():
            root = tk.Tk()
            root.withdraw()
            
            new_url = simpledialog.askstring(
                "Change Server", 
                f"Current: {self.server_url}\n\nNew server URL:",
                initialvalue=self.server_url
            )
            
            if new_url and new_url != self.server_url:
                self.server_url = new_url
                self.save_config()
                
                if messagebox.askyesno("Restart Required", 
                    "Restart SysWatch service to apply changes?"):
                    self.restart_service(None, None)
            
            root.destroy()
        
        threading.Thread(target=show_dialog, daemon=True).start()
    
    def restart_service(self, icon, item):
        def restart():
            try:
                # Kill existing processes
                subprocess.run(['taskkill', '/f', '/im', 'syswatch-agent-windows.exe'], 
                             capture_output=True, check=False)
                
                import time
                time.sleep(2)
                
                # Try to start service
                try:
                    subprocess.run(['sc', 'start', 'SysWatch Agent'], check=True, capture_output=True)
                    self.show_notification("Service restarted")
                except:
                    # Find and start executable directly
                    possible_paths = [
                        "C:/Program Files/SysWatch/syswatch-agent-windows.exe",
                        "C:/Program Files (x86)/SysWatch/syswatch-agent-windows.exe"
                    ]
                    
                    for path in possible_paths:
                        if Path(path).exists():
                            subprocess.Popen([path, self.server_url], 
                                           creationflags=subprocess.CREATE_NO_WINDOW)
                            self.show_notification("Agent restarted")
                            return
                    
                    self.show_notification("Could not restart agent")
                    
            except Exception as e:
                self.show_notification(f"Error: {str(e)}")
        
        threading.Thread(target=restart, daemon=True).start()
    
    def update_agent(self, icon, item):
        if not GUI_AVAILABLE:
            return
            
        def update():
            root = tk.Tk()
            root.withdraw()
            
            if messagebox.askyesno("Update Agent", "Check for and install agent updates?"):
                try:
                    # Find agent executable
                    agent_paths = [
                        "C:/Program Files/SysWatch/syswatch-agent-windows.exe",
                        "C:/Program Files (x86)/SysWatch/syswatch-agent-windows.exe"
                    ]
                    
                    agent_path = None
                    for path in agent_paths:
                        if Path(path).exists():
                            agent_path = path
                            break
                    
                    if agent_path:
                        # Trigger agent update (agent handles its own update process)
                        subprocess.Popen([agent_path, "--check-update"], 
                                       creationflags=subprocess.CREATE_NO_WINDOW)
                        messagebox.showinfo("Update", "Update check started. Agent and tray will restart if update is available.")
                        
                        # Exit tray to allow update
                        root.destroy()
                        self.quit_app(icon, item)
                    else:
                        messagebox.showerror("Error", "Agent executable not found")
                except Exception as e:
                    messagebox.showerror("Error", f"Update failed: {str(e)}")
            
            root.destroy()
        
        threading.Thread(target=update, daemon=True).start()
    
    def view_status(self, icon, item):
        if not GUI_AVAILABLE:
            return
            
        def show_status():
            root = tk.Tk()
            root.withdraw()
            
            # Check if agent is running
            try:
                result = subprocess.run(['tasklist', '/fi', 'imagename eq syswatch-agent-windows.exe'], 
                                      capture_output=True, text=True)
                running = 'syswatch-agent-windows.exe' in result.stdout
                status = "Running" if running else "Not Running"
            except:
                status = "Unknown"
            
            messagebox.showinfo("SysWatch Status", 
                f"Agent Status: {status}\n"
                f"Server: {self.server_url}\n"
                f"Config: {self.config_file}")
            
            root.destroy()
        
        threading.Thread(target=show_status, daemon=True).start()
    
    def show_about(self, icon, item):
        if not GUI_AVAILABLE:
            return
            
        def show_dialog():
            root = tk.Tk()
            root.withdraw()
            
            # Get version from multiple sources
            version = "Unknown"
            try:
                # Try to import from version.py (if embedded)
                from version import VERSION
                version = f"v{VERSION}"
            except ImportError:
                try:
                    # Try to read from agent directory
                    version_file = Path(__file__).parent / "version.py"
                    if version_file.exists():
                        with open(version_file, 'r') as f:
                            content = f.read()
                            import re
                            match = re.search(r'VERSION = "([^"]+)"', content)
                            if match:
                                version = f"v{match.group(1)}"
                except:
                    pass
            
            messagebox.showinfo("About SysWatch", 
                f"SysWatch Agent Tray {version}\n\n"
                f"Server: {self.server_url}\n"
                f"Remote monitoring system")
            
            root.destroy()
        
        threading.Thread(target=show_dialog, daemon=True).start()
    
    def show_notification(self, message):
        if TRAY_AVAILABLE and hasattr(self.icon, 'notify'):
            self.icon.notify(message, "SysWatch")
        else:
            print(f"SysWatch: {message}")
    
    def quit_app(self, icon, item):
        if TRAY_AVAILABLE:
            icon.stop()
        sys.exit(0)
    
    def run_console_mode(self):
        print("SysWatch Tray - Console Mode")
        print(f"Server: {self.server_url}")
        print("Commands: status, restart, quit")
        
        while True:
            try:
                cmd = input("> ").strip().lower()
                if cmd == 'quit':
                    break
                elif cmd == 'status':
                    result = subprocess.run(['tasklist', '/fi', 'imagename eq syswatch-agent-windows.exe'], 
                                          capture_output=True, text=True)
                    running = 'syswatch-agent-windows.exe' in result.stdout
                    print(f"Agent Status: {'Running' if running else 'Not Running'}")
                elif cmd == 'restart':
                    self.restart_service(None, None)
                else:
                    print("Unknown command")
            except KeyboardInterrupt:
                break
    
    def run(self):
        if TRAY_AVAILABLE:
            self.icon.run()
        else:
            self.run_console_mode()

if __name__ == "__main__":
    try:
        app = SysWatchTray()
        app.run()
    except Exception as e:
        # Log error for debugging
        try:
            with open('C:\\temp\\tray_error.log', 'w') as f:
                f.write(f"Error: {e}\n")
                import traceback
                f.write(traceback.format_exc())
        except:
            pass
        print(f"Tray error: {e}")
        input("Press Enter to exit...")
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
            # First try to get server URL from running agent process
            detected_url = self.get_agent_server_url()
            print(f"Detected server URL from process: {detected_url}")
            
            if detected_url:
                self.server_url = detected_url
            else:
                # Fallback to config file
                if self.config_file.exists():
                    with open(self.config_file, 'r') as f:
                        config = json.load(f)
                        self.server_url = config.get('server_url', 'ws://localhost:3000')
                else:
                    self.server_url = 'ws://localhost:3000'
            
            print(f"Final server URL: {self.server_url}")
        except Exception as e:
            print(f"Error loading config: {e}")
            self.server_url = 'ws://localhost:3000'
    
    def get_agent_server_url(self):
        """Get server URL from running agent process"""
        try:
            import subprocess
            import re
            
            print("Attempting to detect server URL from running agent...")
            
            # Method 1: Try tasklist with verbose output
            result = subprocess.run(['tasklist', '/v', '/fi', 'imagename eq syswatch-agent-windows.exe'], 
                                  capture_output=True, text=True)
            print(f"Tasklist output: {result.stdout[:200]}...")
            
            match = re.search(r'ws://[^\s"]+', result.stdout)
            if match:
                print(f"Found URL via tasklist: {match.group(0)}")
                return match.group(0)
            
            # Method 2: Try wmic command line
            result = subprocess.run(['wmic', 'process', 'where', 'name="syswatch-agent-windows.exe"', 
                                   'get', 'commandline', '/format:list'], capture_output=True, text=True)
            print(f"WMIC output: {result.stdout[:200]}...")
            
            match = re.search(r'ws://[^\s"]+', result.stdout)
            if match:
                print(f"Found URL via wmic: {match.group(0)}")
                return match.group(0)
            
            # Method 3: Try PowerShell Get-Process
            result = subprocess.run([
                'powershell', '-Command',
                'Get-Process syswatch-agent-windows -ErrorAction SilentlyContinue | Select-Object CommandLine'
            ], capture_output=True, text=True)
            print(f"PowerShell output: {result.stdout[:200]}...")
            
            match = re.search(r'ws://[^\s"]+', result.stdout)
            if match:
                print(f"Found URL via PowerShell: {match.group(0)}")
                return match.group(0)
                
            print("No server URL found in any process output")
            return None
        except Exception as e:
            print(f"Error getting server URL: {e}")
            return None
    
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
            pystray.MenuItem("Restart Agent", self.restart_service),
            pystray.MenuItem("Update Agent", self.update_agent),
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
                # Kill existing agent processes
                subprocess.run(['taskkill', '/f', '/im', 'syswatch-agent-windows.exe'], 
                             capture_output=True, check=False)
                
                # Wait a moment
                import time
                time.sleep(1)
                
                # Find agent executable in installation directory
                possible_paths = [
                    Path("C:/Program Files/SysWatch/syswatch-agent-windows.exe"),
                    Path("C:/Program Files (x86)/SysWatch/syswatch-agent-windows.exe"),
                    Path(__file__).parent / 'syswatch-agent-windows.exe',
                    Path("syswatch-agent-windows.exe")
                ]
                
                agent_path = None
                for path in possible_paths:
                    if path.exists():
                        agent_path = path
                        break
                
                if agent_path:
                    subprocess.Popen([str(agent_path), self.server_url], 
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                    self.show_notification("Agent restarted successfully")
                else:
                    # Try to restart service instead
                    try:
                        subprocess.run(['sc', 'start', 'SysWatchAgent'], check=True, capture_output=True)
                        self.show_notification("Service restarted successfully")
                    except:
                        self.show_notification("Could not find agent executable or restart service")
                    
            except Exception as e:
                self.show_notification(f"Error restarting agent: {str(e)}")
        
        threading.Thread(target=restart, daemon=True).start()
    
    def update_agent(self, icon, item):
        def update():
            try:
                self.show_notification("Checking for updates...")
                
                # Download latest release
                url = "https://github.com/wslabn/nxtclone/releases/latest/download/syswatch-agent-windows.exe"
                response = subprocess.run([
                    'powershell', '-Command', 
                    f'New-Item -ItemType Directory -Force -Path "C:\\temp"; Invoke-WebRequest -Uri "{url}" -OutFile "C:\\temp\\syswatch-update.exe"'
                ], capture_output=True, text=True)
                
                if response.returncode == 0:
                    self.show_notification("Update downloaded, installing...")
                    
                    # Find installation directory
                    target_exe = None
                    install_paths = [
                        "C:/Program Files/SysWatch/syswatch-agent-windows.exe",
                        "C:/Program Files (x86)/SysWatch/syswatch-agent-windows.exe"
                    ]
                    
                    for install_path in install_paths:
                        if Path(install_path).exists():
                            target_exe = install_path
                            break
                    
                    if target_exe:
                        # Download and use external updater
                        updater_url = "https://github.com/wslabn/nxtclone/releases/latest/download/updater.py"
                        subprocess.run([
                            'powershell', '-Command',
                            f'Invoke-WebRequest -Uri "{updater_url}" -OutFile "C:\\temp\\updater.py"'
                        ], capture_output=True)
                        
                        # Launch external updater
                        subprocess.Popen([
                            'python', 'C:\\temp\\updater.py', 
                            'C:\\temp\\syswatch-update.exe', target_exe
                        ], creationflags=subprocess.CREATE_NO_WINDOW)
                        
                        self.show_notification("Update in progress...")
                    else:
                        self.show_notification("Installation not found")
                else:
                    self.show_notification("Update download failed")
                    
            except Exception as e:
                self.show_notification(f"Update failed: {str(e)}")
        
        threading.Thread(target=update, daemon=True).start()
    
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
                # Try to import version from version.py (embedded in executable)
                try:
                    from version import VERSION
                    version = VERSION
                except ImportError:
                    version = "Unknown"
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
        # Check if another instance is already running
        import psutil
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] == 'syswatch-tray.exe' and proc.info['pid'] != current_pid:
                    print("Another instance of SysWatch Tray is already running")
                    sys.exit(0)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        app = SysWatchTray()
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Tray application error: {e}")
        sys.exit(1)
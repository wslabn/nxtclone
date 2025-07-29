#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import signal
from pathlib import Path

class SysWatchLinuxTray:
    def __init__(self):
        self.config_file = Path("/opt/syswatch/tray_config.json")
        self.load_config()
        
        # Try GUI first, fallback to CLI
        self.has_gui = self.check_gui()
        
        if self.has_gui:
            self.init_gui()
        else:
            self.init_cli()
    
    def check_gui(self):
        """Check if GUI is available"""
        return os.environ.get('DISPLAY') is not None or os.environ.get('WAYLAND_DISPLAY') is not None
    
    def load_config(self):
        try:
            # First try to get server URL from running agent process
            self.server_url = self.get_agent_server_url()
            
            # Fallback to config file
            if not self.server_url or self.server_url == 'ws://localhost:3000':
                if self.config_file.exists():
                    with open(self.config_file, 'r') as f:
                        config = json.load(f)
                        self.server_url = config.get('server_url', 'ws://localhost:3000')
                else:
                    self.server_url = 'ws://localhost:3000'
        except:
            self.server_url = 'ws://localhost:3000'
    
    def get_agent_server_url(self):
        """Get server URL from running agent process"""
        try:
            import subprocess
            # Get command line of running agent process
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if 'syswatch-agent-linux' in line and 'ws://' in line:
                    # Extract URL from command line
                    parts = line.split()
                    for part in parts:
                        if part.startswith('ws://'):
                            return part
            return None
        except:
            return None
    
    def save_config(self):
        try:
            os.makedirs(self.config_file.parent, exist_ok=True)
            config = {'server_url': self.server_url}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def init_gui(self):
        """Initialize GUI tray (if available)"""
        try:
            import tkinter as tk
            from tkinter import messagebox, simpledialog
            import threading
            
            # Try to use system tray
            try:
                import pystray
                from PIL import Image, ImageDraw
                self.create_gui_tray()
                return
            except ImportError:
                pass
            
            # Fallback to simple GUI window
            self.create_simple_gui()
            
        except ImportError:
            print("GUI not available, falling back to CLI mode")
            self.init_cli()
    
    def create_gui_tray(self):
        """Create system tray icon"""
        import pystray
        from PIL import Image, ImageDraw
        
        # Create icon
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill='white')
        draw.text((20, 25), "SW", fill='blue')
        
        menu = pystray.Menu(
            pystray.MenuItem("SysWatch Agent", self.show_about, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Change Server", self.change_server_gui),
            pystray.MenuItem("Restart Service", self.restart_service),
            pystray.MenuItem("View Logs", self.view_logs),
            pystray.MenuItem("Service Status", self.show_status),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("About", self.show_about),
            pystray.MenuItem("Exit", self.quit_app)
        )
        
        self.icon = pystray.Icon("SysWatch", image, "SysWatch Agent", menu)
        self.icon.run()
    
    def create_simple_gui(self):
        """Create simple GUI window"""
        import tkinter as tk
        from tkinter import ttk
        
        root = tk.Tk()
        root.title("SysWatch Agent Control")
        root.geometry("400x300")
        
        # Server info
        tk.Label(root, text=f"Server: {self.server_url}", font=('Arial', 10)).pack(pady=10)
        
        # Buttons
        ttk.Button(root, text="Change Server", command=self.change_server_gui).pack(pady=5)
        ttk.Button(root, text="Restart Service", command=self.restart_service).pack(pady=5)
        ttk.Button(root, text="View Logs", command=self.view_logs).pack(pady=5)
        ttk.Button(root, text="Service Status", command=self.show_status).pack(pady=5)
        ttk.Button(root, text="About", command=self.show_about).pack(pady=5)
        ttk.Button(root, text="Exit", command=root.quit).pack(pady=5)
        
        root.mainloop()
    
    def init_cli(self):
        """Initialize CLI interface"""
        print("SysWatch Agent Control (CLI Mode)")
        print("=" * 40)
        
        while True:
            print(f"\nCurrent server: {self.server_url}")
            print("\nOptions:")
            print("1. Change server URL")
            print("2. Restart service")
            print("3. View logs")
            print("4. Service status")
            print("5. About")
            print("6. Exit")
            
            try:
                choice = input("\nEnter choice (1-6): ").strip()
                
                if choice == '1':
                    self.change_server_cli()
                elif choice == '2':
                    self.restart_service()
                elif choice == '3':
                    self.view_logs()
                elif choice == '4':
                    self.show_status()
                elif choice == '5':
                    self.show_about()
                elif choice == '6':
                    break
                else:
                    print("Invalid choice")
                    
            except KeyboardInterrupt:
                break
    
    def change_server_gui(self):
        """Change server URL (GUI)"""
        import tkinter as tk
        from tkinter import simpledialog
        
        root = tk.Tk()
        root.withdraw()
        
        new_url = simpledialog.askstring(
            "Change Server",
            f"Current: {self.server_url}\n\nEnter new server URL:",
            initialvalue=self.server_url
        )
        
        if new_url and new_url != self.server_url:
            self.server_url = new_url
            self.save_config()
            print(f"Server URL changed to: {new_url}")
            
            from tkinter import messagebox
            if messagebox.askyesno("Restart Required", 
                "Server URL changed. Restart service to apply changes?"):
                self.restart_service()
        
        root.destroy()
    
    def change_server_cli(self):
        """Change server URL (CLI)"""
        print(f"\nCurrent server: {self.server_url}")
        new_url = input("Enter new server URL (or press Enter to cancel): ").strip()
        
        if new_url and new_url != self.server_url:
            self.server_url = new_url
            self.save_config()
            print(f"Server URL changed to: {new_url}")
            
            restart = input("Restart service now? (y/N): ").strip().lower()
            if restart == 'y':
                self.restart_service()
    
    def restart_service(self):
        """Restart the SysWatch service"""
        try:
            print("Restarting SysWatch service...")
            result = subprocess.run(['sudo', 'systemctl', 'restart', 'syswatch-agent'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Service restarted successfully")
            else:
                print(f"Failed to restart service: {result.stderr}")
                
        except Exception as e:
            print(f"Error restarting service: {e}")
    
    def view_logs(self):
        """View service logs"""
        try:
            print("Opening logs...")
            subprocess.run(['journalctl', '-u', 'syswatch-agent', '-f'])
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error viewing logs: {e}")
    
    def show_status(self):
        """Show service status"""
        try:
            result = subprocess.run(['systemctl', 'status', 'syswatch-agent'], 
                                  capture_output=True, text=True)
            print("\nService Status:")
            print("-" * 20)
            print(result.stdout)
            
        except Exception as e:
            print(f"Error getting status: {e}")
    
    def show_about(self):
        """Show about information"""
        try:
            # Try to import version from version.py (embedded in executable)
            try:
                from version import VERSION
                version = VERSION
            except ImportError:
                version = "Unknown"
        except:
            version = "Unknown"
        
        about_text = f"""
SysWatch Agent v{version}

Server: {self.server_url}
Install Path: /opt/syswatch/
Service: syswatch-agent

Remote monitoring and management system
© 2025 SysWatch
        """
        
        if self.has_gui:
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showinfo("About SysWatch Agent", about_text)
                root.destroy()
            except:
                print(about_text)
        else:
            print(about_text)
    
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        if hasattr(self, 'icon'):
            self.icon.stop()
        sys.exit(0)

def main():
    # Handle signals
    def signal_handler(sig, frame):
        print("\nExiting...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        app = SysWatchLinuxTray()
    except Exception as e:
        print(f"Error starting SysWatch tray: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
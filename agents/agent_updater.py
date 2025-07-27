import requests
import os
import sys
import subprocess
import tempfile
import zipfile
import shutil
from pathlib import Path

class AgentUpdater:
    def __init__(self, repo_owner="wslabn", repo_name="nxtclone"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version = self.get_current_version()
        
    def get_current_version(self):
        try:
            # Try to read version from a version file
            version_file = Path(__file__).parent / "version.txt"
            if version_file.exists():
                return version_file.read_text().strip()
            return "1.0.0"
        except:
            return "1.0.0"
    
    def check_for_updates(self):
        try:
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
            headers = {"User-Agent": "syswatch-agent-updater"}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            release = response.json()
            latest_version = release["tag_name"].replace("v", "")
            
            # Get platform-specific download URL
            download_url = self.get_platform_download_url(release)
            
            return {
                "has_update": self.compare_versions(latest_version, self.current_version) > 0,
                "current_version": self.current_version,
                "latest_version": latest_version,
                "download_url": download_url,
                "release_notes": release.get("body", "")
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_platform_download_url(self, release):
        """Get the correct download URL for current platform"""
        assets = release.get("assets", [])
        
        if sys.platform.startswith('win'):
            # Look for Windows executable
            for asset in assets:
                if asset["name"] == "syswatch-agent-windows.exe":
                    return asset["browser_download_url"]
        else:
            # Look for Linux executable
            for asset in assets:
                if asset["name"] == "syswatch-agent-linux":
                    return asset["browser_download_url"]
        
        # Fallback to source code
        return release["zipball_url"]
    
    def compare_versions(self, a, b):
        a_parts = [int(x) for x in a.split('.')]
        b_parts = [int(x) for x in b.split('.')]
        
        # Pad shorter version with zeros
        max_len = max(len(a_parts), len(b_parts))
        a_parts.extend([0] * (max_len - len(a_parts)))
        b_parts.extend([0] * (max_len - len(b_parts)))
        
        for i in range(max_len):
            if a_parts[i] > b_parts[i]:
                return 1
            elif a_parts[i] < b_parts[i]:
                return -1
        return 0
    
    def download_and_update(self, download_url):
        try:
            print("Downloading update...")
            
            # Check if this is a direct executable download
            if download_url.endswith(('.exe', '-linux')):
                return self.download_executable_update(download_url)
            else:
                return self.download_source_update(download_url)
                
        except Exception as e:
            print(f"Update failed: {e}")
            return False
    
    def download_executable_update(self, download_url):
        """Download and replace executable"""
        try:
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            current_exe = sys.argv[0]
            backup_exe = current_exe + ".backup"
            
            # Create backup
            shutil.copy2(current_exe, backup_exe)
            
            # Download new executable
            with open(current_exe + ".new", 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Make executable (Linux)
            if not sys.platform.startswith('win'):
                os.chmod(current_exe + ".new", 0o755)
            
            # Replace current executable
            if sys.platform.startswith('win'):
                # Windows: rename current, move new
                os.rename(current_exe, current_exe + ".old")
                os.rename(current_exe + ".new", current_exe)
                
                # Update tray app if it exists
                self.update_tray_app_if_exists()
            else:
                # Linux: direct replace
                os.rename(current_exe + ".new", current_exe)
                
                # Update control app if it exists
                self.update_control_app_if_exists()
            
            print("Executable updated successfully")
            return True
            
        except Exception as e:
            print(f"Executable update failed: {e}")
            # Restore backup if available
            if os.path.exists(backup_exe):
                shutil.copy2(backup_exe, current_exe)
            return False
    
    def download_source_update(self, download_url):
        """Download and update from source (fallback)"""
        try:
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, "update.zip")
                
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                extracted_folders = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
                if not extracted_folders:
                    raise Exception("No extracted folder found")
                
                source_dir = os.path.join(temp_dir, extracted_folders[0], "agents")
                current_dir = Path(__file__).parent
                
                if os.path.exists(source_dir):
                    for file in os.listdir(source_dir):
                        if file.endswith('.py') or file == 'version.txt':
                            src = os.path.join(source_dir, file)
                            dst = current_dir / file
                            shutil.copy2(src, dst)
                            print(f"Updated {file}")
                
                return True
                
        except Exception as e:
            print(f"Source update failed: {e}")
            return False
    
    def update_tray_app_if_exists(self):
        """Update Windows tray app if it exists"""
        try:
            install_dir = os.path.dirname(sys.argv[0])
            tray_path = os.path.join(install_dir, "syswatch-tray.exe")
            
            if os.path.exists(tray_path):
                print("Updating tray application...")
                # Download latest tray app
                url = f"https://github.com/{self.repo_owner}/{self.repo_name}/releases/latest/download/syswatch-tray.exe"
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Replace tray app
                backup_path = tray_path + ".backup"
                shutil.copy2(tray_path, backup_path)
                
                with open(tray_path + ".new", 'wb') as f:
                    f.write(response.content)
                
                os.rename(tray_path, tray_path + ".old")
                os.rename(tray_path + ".new", tray_path)
                print("Tray application updated successfully")
        except Exception as e:
            print(f"Tray app update failed: {e}")
    
    def update_control_app_if_exists(self):
        """Update Linux control app if it exists"""
        try:
            install_dir = os.path.dirname(sys.argv[0])
            control_path = os.path.join(install_dir, "syswatch-control")
            
            if os.path.exists(control_path):
                print("Updating control application...")
                # Download latest control app
                url = f"https://github.com/{self.repo_owner}/{self.repo_name}/releases/latest/download/syswatch-control"
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Replace control app
                backup_path = control_path + ".backup"
                shutil.copy2(control_path, backup_path)
                
                with open(control_path + ".new", 'wb') as f:
                    f.write(response.content)
                
                os.chmod(control_path + ".new", 0o755)
                os.rename(control_path, control_path + ".old")
                os.rename(control_path + ".new", control_path)
                print("Control application updated successfully")
        except Exception as e:
            print(f"Control app update failed: {e}")
    
    def restart_agent(self):
        """Restart the current agent process"""
        try:
            # Get current script path and arguments
            script_path = sys.argv[0]
            args = sys.argv[1:]
            
            # Start new process directly (skip service restart for both platforms)
            if sys.platform.startswith('win'):
                subprocess.Popen([script_path] + args, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen([script_path] + args)
            
            print("Process restart initiated")
            
            # Exit current process
            sys.exit(0)
            
        except Exception as e:
            print(f"Restart failed: {e}")
            return False
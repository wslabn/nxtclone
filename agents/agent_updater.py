import requests
import os
import sys
import subprocess
import tempfile
import zipfile
import shutil
import json
import time
from pathlib import Path

class AgentUpdater:
    def __init__(self, repo_owner="wslabn", repo_name="nxtclone"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version = self.get_current_version()
        
    def get_current_version(self):
        try:
            # Try to import version from version.py (embedded in executable)
            try:
                from version import VERSION
                print(f"Read version from version.py: {VERSION}")
                return VERSION
            except ImportError:
                print("version.py not found, trying fallback methods")
            
            # Fallback: try package.json (for source installs)
            package_file = Path(__file__).parent / ".." / "package.json"
            print(f"Looking for package.json at: {package_file}")
            
            if package_file.exists():
                print(f"Found package.json, reading version...")
                with open(package_file, 'r') as f:
                    package_data = json.load(f)
                    version = package_data.get('version', '1.0.0')
                    print(f"Read version from package.json: {version}")
                    return version
            
            print("No version source found")
            return "1.0.0"
        except Exception as e:
            print(f"Error reading version: {e}")
            return "1.0.0"
    
    def check_for_updates(self):
        try:
            # Refresh current version on each check
            current_version = self.get_current_version()
            
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
            headers = {"User-Agent": "syswatch-agent-updater"}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            release = response.json()
            latest_version = release["tag_name"].replace("v", "")
            
            # Get platform-specific download URL
            download_url = self.get_platform_download_url(release)
            
            return {
                "has_update": self.compare_versions(latest_version, current_version) > 0,
                "current_version": current_version,
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
            print(f"Downloading update from: {download_url}")
            
            # Check if this is a direct executable download
            if download_url.endswith(('.exe', '-linux')):
                print("Starting executable update process...")
                result = self.download_executable_update(download_url)
                print(f"Executable update result: {result}")
                return result
            else:
                print("Starting source update process...")
                result = self.download_source_update(download_url)
                print(f"Source update result: {result}")
                return result
                
        except Exception as e:
            print(f"Update failed with exception: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False
    
    def download_executable_update(self, download_url):
        """Download and replace executable using external updater"""
        try:
            current_exe = sys.argv[0]
            new_exe = current_exe + ".new"
            
            # Download new executable
            print("Downloading new executable...")
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(new_exe, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if sys.platform.startswith('win'):
                # Windows: Use external updater
                return self.update_with_external_updater(new_exe, current_exe)
            else:
                # Linux: direct replace (works fine on Linux)
                os.chmod(new_exe, 0o755)
                os.rename(new_exe, current_exe)
                self.update_control_app_if_exists()
                print("Executable updated successfully")
                return True
            
        except Exception as e:
            print(f"Executable update failed: {e}")
            # Clean up downloaded file
            if os.path.exists(new_exe):
                os.remove(new_exe)
            return False
    
    def update_with_external_updater(self, new_exe, current_exe):
        """Simple file replacement - no admin needed in LOCALAPPDATA"""
        try:
            # Update tray app if it exists
            self.update_tray_app_if_exists()
            
            # Create log file
            log_file = "C:\\temp\\syswatch_update.log"
            with open(log_file, 'w') as f:
                f.write(f"Starting simple update at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"New exe: {new_exe}\n")
                f.write(f"Current exe: {current_exe}\n")
            
            print("Performing direct file replacement...")
            
            # Stop service
            subprocess.run(['sc', 'stop', 'SysWatch Agent'], capture_output=True)
            subprocess.run(['taskkill', '/f', '/im', 'syswatch-agent-windows.exe'], capture_output=True)
            time.sleep(3)
            
            # Backup current file
            if os.path.exists(current_exe):
                shutil.copy2(current_exe, current_exe + ".backup")
                with open(log_file, 'a') as f:
                    f.write("Created backup file\n")
            
            # Replace with new file
            shutil.copy2(new_exe, current_exe)
            os.remove(new_exe)
            
            with open(log_file, 'a') as f:
                f.write("File replacement completed\n")
            
            # Start service
            time.sleep(2)
            subprocess.run(['sc', 'start', 'SysWatch Agent'], capture_output=True)
            
            with open(log_file, 'a') as f:
                f.write("Service restarted\n")
                f.write("Update completed successfully\n")
            
            print("Update completed successfully")
            return True
            
        except Exception as e:
            with open(log_file, 'a') as f:
                f.write(f"Update failed: {e}\n")
            print(f"Update failed: {e}")
            return False
    
    def create_embedded_updater(self, updater_path):
        """Create embedded updater script as fallback"""
        updater_code = '''#!/usr/bin/env python3
import sys, os, time, subprocess, shutil

def main():
    if len(sys.argv) != 3: sys.exit(1)
    new_exe, target_exe = sys.argv[1], sys.argv[2]
    
    # Ensure temp directory exists
    if not os.path.exists("C:\\temp"):
        os.makedirs("C:\\temp")
    
    # Log to temp directory
    log_file = "C:\\temp\\updater.log"
    with open(log_file, "w") as f:
        f.write(f"Starting service-based update: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
    
    # Create batch script for service to execute
    service_script = "C:\\temp\\service_update.bat"
    with open(service_script, "w") as f:
        f.write("@echo off\\n")
        f.write("echo Service update starting...\\n")
        f.write(f"copy \"{new_exe}\" \"{target_exe}.new\" >nul 2>&1\\n")
        f.write(f"if exist \"{target_exe}\" move \"{target_exe}\" \"{target_exe}.backup\" >nul 2>&1\\n")
        f.write(f"move \"{target_exe}.new\" \"{target_exe}\" >nul 2>&1\\n")
        f.write(f"del \"{new_exe}\" >nul 2>&1\\n")
        f.write("echo File replacement completed\\n")
    
    # Stop service and let it handle file replacement
    with open(log_file, "a") as f:
        f.write("Stopping service for update...\\n")
    
    # Use sc to stop service and run update script
    subprocess.run(['sc', 'stop', 'SysWatch Agent'], capture_output=True)
    time.sleep(3)
    
    # Execute file replacement as system
    result = subprocess.run([service_script], capture_output=True, text=True, shell=True)
    
    with open(log_file, "a") as f:
        f.write(f"Update script result: {result.returncode}\\n")
        if result.stdout: f.write(f"Output: {result.stdout}\\n")
        if result.stderr: f.write(f"Error: {result.stderr}\\n")
    
    # Start service
    time.sleep(2)
    subprocess.run(['sc', 'start', 'SysWatch Agent'], capture_output=True)
    
    with open(log_file, "a") as f:
        f.write("Service restart completed\\n")
    
    # Cleanup
    try: 
        os.remove(service_script)
        os.remove(__file__)
    except: pass

if __name__ == "__main__": main()
'''
        with open(updater_path, 'w') as f:
            f.write(updater_code)
    
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
                
                # Kill existing tray processes
                subprocess.run(['taskkill', '/f', '/im', 'syswatch-tray.exe'], 
                             capture_output=True, check=False)
                
                os.rename(tray_path, tray_path + ".old")
                os.rename(tray_path + ".new", tray_path)
                print("Tray application updated successfully")
                
                # Restart tray app after a delay
                import time
                time.sleep(2)
                subprocess.Popen([tray_path], creationflags=subprocess.CREATE_NO_WINDOW)
                print("Tray application restarted")
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
        """Restart the current agent process with robust error handling"""
        try:
            if sys.platform.startswith('win'):
                return self.restart_windows_service()
            else:
                return self.restart_linux_service()
        except Exception as e:
            print(f"Restart failed: {e}")
            return False
    
    def restart_windows_service(self):
        """Restart Windows service - not used with external updater"""
        # External updater handles service restart
        print("Service restart handled by external updater")
        return True
    
    def create_robust_update_script(self, script_path, service_name):
        """Create enhanced batch script with NSSM failure handling"""
        install_dir = os.path.dirname(sys.argv[0])
        nssm_path = os.path.join(install_dir, "nssm.exe")
        
        with open(script_path, 'w') as f:
            f.write('@echo off\n')
            f.write('echo Starting robust agent update...\n')
            f.write('timeout /t 3 /nobreak >nul\n')
            
            # Replace executable
            f.write(f'echo Replacing agent executable...\n')
            f.write(f'move "{sys.argv[0] + ".new"}" "{sys.argv[0]}"\n')
            f.write('if errorlevel 1 (\n')
            f.write('    echo Failed to replace executable\n')
            f.write('    goto cleanup\n')
            f.write(')\n')
            
            # Try multiple restart methods
            f.write('echo Attempting service restart...\n')
            
            # Method 1: Try sc commands first (more reliable)
            f.write(f'sc stop "{service_name}" >nul 2>&1\n')
            f.write('timeout /t 5 /nobreak >nul\n')
            f.write(f'sc start "{service_name}" >nul 2>&1\n')
            f.write('if not errorlevel 1 (\n')
            f.write('    echo Service restarted successfully with sc\n')
            f.write('    goto cleanup\n')
            f.write(')\n')
            
            # Method 2: Try NSSM if sc fails
            f.write('echo SC restart failed, trying NSSM...\n')
            f.write(f'"{nssm_path}" stop "{service_name}" >nul 2>&1\n')
            f.write('timeout /t 5 /nobreak >nul\n')
            f.write(f'"{nssm_path}" start "{service_name}" >nul 2>&1\n')
            f.write('if not errorlevel 1 (\n')
            f.write('    echo Service restarted successfully with NSSM\n')
            f.write('    goto cleanup\n')
            f.write(')\n')
            
            # Method 3: Try net commands as fallback
            f.write('echo NSSM restart failed, trying net commands...\n')
            f.write(f'net stop "{service_name}" >nul 2>&1\n')
            f.write('timeout /t 5 /nobreak >nul\n')
            f.write(f'net start "{service_name}" >nul 2>&1\n')
            f.write('if not errorlevel 1 (\n')
            f.write('    echo Service restarted successfully with net\n')
            f.write('    goto cleanup\n')
            f.write(')\n')
            
            # Method 4: Try to reinstall service if all else fails
            f.write('echo All restart methods failed, attempting service reinstall...\n')
            f.write(f'"{nssm_path}" remove "{service_name}" confirm >nul 2>&1\n')
            f.write('timeout /t 2 /nobreak >nul\n')
            f.write(f'"{nssm_path}" install "{service_name}" "{sys.argv[0]}" >nul 2>&1\n')
            f.write(f'"{nssm_path}" set "{service_name}" Start SERVICE_AUTO_START >nul 2>&1\n')
            f.write(f'"{nssm_path}" start "{service_name}" >nul 2>&1\n')
            f.write('if not errorlevel 1 (\n')
            f.write('    echo Service reinstalled and started successfully\n')
            f.write(') else (\n')
            f.write('    echo All restart methods failed - manual intervention required\n')
            f.write(')\n')
            
            # Cleanup
            f.write(':cleanup\n')
            f.write('echo Update process completed\n')
            f.write(f'del "{script_path}" >nul 2>&1\n')
            f.write(f'del "{sys.argv[0] + ".backup"}" >nul 2>&1\n')
    
    def restart_service_with_retry(self, service_name, max_retries=3):
        """Restart service with multiple methods and retry logic"""
        methods = [
            lambda: self.restart_with_sc(service_name),
            lambda: self.restart_with_nssm(service_name),
            lambda: self.restart_with_net(service_name)
        ]
        
        for attempt in range(max_retries):
            for i, method in enumerate(methods):
                try:
                    print(f"Restart attempt {attempt + 1}, method {i + 1}")
                    if method():
                        print(f"Service restarted successfully with method {i + 1}")
                        return True
                except Exception as e:
                    print(f"Method {i + 1} failed: {e}")
                    continue
            
            if attempt < max_retries - 1:
                print(f"All methods failed, waiting before retry {attempt + 2}...")
                import time
                time.sleep(5)
        
        print("All restart attempts failed")
        return False
    
    def restart_with_sc(self, service_name):
        """Restart using sc commands"""
        stop_result = subprocess.run(['sc', 'stop', service_name], 
                                   capture_output=True, text=True, timeout=30)
        
        # Wait for service to stop
        import time
        time.sleep(5)
        
        start_result = subprocess.run(['sc', 'start', service_name], 
                                    capture_output=True, text=True, timeout=30)
        
        return start_result.returncode == 0
    
    def restart_with_nssm(self, service_name):
        """Restart using NSSM (with error handling)"""
        install_dir = os.path.dirname(sys.argv[0])
        nssm_path = os.path.join(install_dir, "nssm.exe")
        
        if not os.path.exists(nssm_path):
            return False
        
        try:
            stop_result = subprocess.run([nssm_path, 'stop', service_name], 
                                       capture_output=True, text=True, timeout=30)
            
            # Wait for service to stop
            import time
            time.sleep(5)
            
            start_result = subprocess.run([nssm_path, 'start', service_name], 
                                        capture_output=True, text=True, timeout=30)
            
            return start_result.returncode == 0
        except subprocess.TimeoutExpired:
            print("NSSM command timed out")
            return False
        except Exception as e:
            print(f"NSSM restart failed: {e}")
            return False
    
    def restart_with_net(self, service_name):
        """Restart using net commands"""
        try:
            stop_result = subprocess.run(['net', 'stop', service_name], 
                                       capture_output=True, text=True, timeout=30)
            
            # Wait for service to stop
            import time
            time.sleep(5)
            
            start_result = subprocess.run(['net', 'start', service_name], 
                                        capture_output=True, text=True, timeout=30)
            
            return start_result.returncode == 0
        except Exception as e:
            print(f"Net restart failed: {e}")
            return False
    
    def restart_linux_service(self):
        """Restart Linux service with retry logic (user or system)"""
        try:
            # Detect installation type
            if os.path.exists('/opt/syswatch'):
                # System installation
                result = subprocess.run(['sudo', 'systemctl', 'restart', 'syswatch-agent'], 
                                      capture_output=True, text=True, timeout=30)
                service_type = "system"
            else:
                # User installation
                result = subprocess.run(['systemctl', '--user', 'restart', 'syswatch-agent'], 
                                      capture_output=True, text=True, timeout=30)
                service_type = "user"
            
            if result.returncode == 0:
                print(f"Linux {service_type} service restarted successfully")
                return True
            else:
                print(f"Linux {service_type} service restart failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"Linux service restart failed: {e}")
            return False
    
    def create_update_task(self, task_name, updater_script, new_exe, current_exe):
        """Create or update scheduled task for agent updates"""
        try:
            # Delete existing task if it exists
            subprocess.run(['schtasks', '/delete', '/tn', task_name, '/f'], 
                         capture_output=True)
            
            # Create new task with SYSTEM privileges
            cmd = [
                'schtasks', '/create', '/tn', task_name,
                '/tr', f'python "{updater_script}" "{new_exe}" "{current_exe}"',
                '/sc', 'once', '/st', '00:00',
                '/ru', 'SYSTEM', '/f'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Created scheduled task: {task_name}")
                return True
            else:
                print(f"Failed to create task: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Task creation failed: {e}")
            return False
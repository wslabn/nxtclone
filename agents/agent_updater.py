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
            # First try embedded version.txt (for executables)
            version_file = Path(__file__).parent / "version.txt"
            print(f"Looking for embedded version.txt at: {version_file}")
            
            if version_file.exists():
                version = version_file.read_text().strip()
                print(f"Read version from embedded file: {version}")
                return version
            
            # Fallback: try package.json (for source installs)
            package_file = Path(__file__).parent / ".." / "package.json"
            print(f"Looking for package.json at: {package_file}")
            
            if package_file.exists():
                print(f"Found package.json, reading version...")
                import json
                with open(package_file, 'r') as f:
                    package_data = json.load(f)
                    version = package_data.get('version', '1.0.0')
                    print(f"Read version from package.json: {version}")
                    return version
            
            print("No version file found")
            return "1.0.0"
        except Exception as e:
            print(f"Error reading version: {e}")
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
            
            # Replace current executable using batch script for Windows
            if sys.platform.startswith('win'):
                # Create batch script to replace file after exit
                batch_script = current_exe + ".update.bat"
                with open(batch_script, 'w') as f:
                    f.write('@echo off\n')
                    f.write('timeout /t 2 /nobreak >nul\n')
                    f.write(f'move "{current_exe + ".new"}" "{current_exe}"\n')
                    f.write(f'sc start "SysWatch Agent"\n')
                    f.write(f'del "{batch_script}"\n')
                
                # The batch script will run after we exit
                print("Update script created, will replace executable after exit")
                
                # Update tray app if it exists
                self.update_tray_app_if_exists()
            else:
                # Linux: direct replace (works fine on Linux)
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
        """Restart Windows service with NSSM failure handling"""
        service_name = "SysWatchAgent"  # Updated service name
        
        # Check if update batch script exists
        script_path = sys.argv[0] + ".update.bat"
        if os.path.exists(script_path):
            print("Running update script with robust restart...")
            # Create enhanced batch script with NSSM failure handling
            self.create_robust_update_script(script_path, service_name)
            subprocess.Popen([script_path], shell=True)
            print("Enhanced update script started")
            sys.exit(0)
        else:
            # Normal service restart with retry logic
            return self.restart_service_with_retry(service_name)
    
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
        """Restart Linux service with retry logic"""
        try:
            result = subprocess.run(['sudo', 'systemctl', 'restart', 'syswatch-agent'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("Linux service restarted successfully")
                return True
            else:
                print(f"Linux service restart failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"Linux service restart failed: {e}")
            return False
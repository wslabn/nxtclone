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
            headers = {"User-Agent": "nxtclone-agent-updater"}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            release = response.json()
            latest_version = release["tag_name"].replace("v", "")
            
            return {
                "has_update": self.compare_versions(latest_version, self.current_version) > 0,
                "current_version": self.current_version,
                "latest_version": latest_version,
                "download_url": release["zipball_url"],
                "release_notes": release.get("body", "")
            }
        except Exception as e:
            return {"error": str(e)}
    
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
            
            # Download the release
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Create temp directory
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, "update.zip")
                
                # Save zip file
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extract zip
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find the extracted folder (GitHub creates a folder with repo name)
                extracted_folders = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
                if not extracted_folders:
                    raise Exception("No extracted folder found")
                
                source_dir = os.path.join(temp_dir, extracted_folders[0], "agents")
                current_dir = Path(__file__).parent
                
                # Copy new agent files
                if os.path.exists(source_dir):
                    for file in os.listdir(source_dir):
                        if file.endswith('.py') or file == 'version.txt':
                            src = os.path.join(source_dir, file)
                            dst = current_dir / file
                            shutil.copy2(src, dst)
                            print(f"Updated {file}")
                
                print("Update completed. Restarting agent...")
                return True
                
        except Exception as e:
            print(f"Update failed: {e}")
            return False
    
    def restart_agent(self):
        """Restart the current agent process"""
        try:
            # Get current script path and arguments
            script_path = sys.argv[0]
            args = sys.argv[1:]
            
            # Start new process
            if sys.platform.startswith('win'):
                subprocess.Popen([sys.executable, script_path] + args, 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([sys.executable, script_path] + args)
            
            # Exit current process
            sys.exit(0)
            
        except Exception as e:
            print(f"Restart failed: {e}")
            return False
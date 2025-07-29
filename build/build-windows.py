import PyInstaller.__main__
import os
import shutil

def build_windows_agent():
    # Read version from package.json and create version.py
    import json
    try:
        with open('../package.json', 'r') as f:
            package_data = json.load(f)
            version = package_data.get('version', '1.0.0')
        
        # Create version.py file
        with open('../agents/version.py', 'w') as f:
            f.write(f'# This file is auto-generated during build\nVERSION = "{version}"\n')
        print(f"Version {version} embedded in version.py")
    except Exception as e:
        print(f"Error reading version: {e}")
        with open('../agents/version.py', 'w') as f:
            f.write('# This file is auto-generated during build\nVERSION = "1.0.0"\n')
    
    # Create icon first
    try:
        import subprocess
        subprocess.run(['python', 'create_icon.py'], check=True)
        print("Icon created successfully!")
    except Exception as e:
        print(f"Icon creation failed: {e}")
    
    # Build the Windows agent executable
    import sys
    separator = ';' if sys.platform == 'win32' else ':'
    
    PyInstaller.__main__.run([
        '--onefile',
        '--name=syswatch-agent-windows',
        f'--add-data=../agents/version.py{separator}.',
        f'--add-data=../agents/agent_updater.py{separator}.',
        f'--add-data=../agents/windows_agent.py{separator}.',
        '--hidden-import=win32timezone',
        '../agents/windows_agent.py'
    ])
    
    print("Windows agent built successfully!")
    
    # Install tray dependencies
    try:
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pystray', 'pillow'], check=True)
    except Exception as e:
        print(f"Warning: Failed to install tray dependencies: {e}")
    
    # Build tray application
    try:
        PyInstaller.__main__.run([
            '--onefile',
            '--noconsole',
            '--name=syswatch-tray',
            f'--add-data=../agents/version.py{separator}.',
            '--hidden-import=pystray',
            '--hidden-import=PIL',
            '--hidden-import=tkinter',
            '../agents/windows_tray.py'
        ])
        print("Windows tray application built successfully!")
    except Exception as e:
        print(f"Warning: Tray application build failed: {e}")
    
    print("Windows tray application built successfully!")
    
    # Download NSSM
    try:
        import urllib.request
        import zipfile
        print("Downloading NSSM...")
        urllib.request.urlretrieve('https://nssm.cc/release/nssm-2.24.zip', 'nssm.zip')
        with zipfile.ZipFile('nssm.zip', 'r') as zip_ref:
            zip_ref.extract('nssm-2.24/win64/nssm.exe', '.')
        shutil.move('nssm-2.24/win64/nssm.exe', 'dist/nssm.exe')
        shutil.rmtree('nssm-2.24', ignore_errors=True)
        os.remove('nssm.zip')
        print("NSSM downloaded successfully!")
    except Exception as e:
        print(f"Warning: NSSM download failed: {e}")
    
    # Build installer with NSIS
    try:
        import subprocess
        subprocess.run(['makensis', 'installer.nsi'], check=True)
        print("Windows installer built successfully!")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("NSIS not found - installer not built. Agent executable created.")
        print("To build installer manually: makensis installer.nsi")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    build_windows_agent()
import PyInstaller.__main__
import os
import shutil

def build_windows_agent():
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
        '--name=syswatch-agent',
        f'--add-data=../agents/version.txt{separator}.',
        f'--add-data=../agents/agent_updater.py{separator}.',
        f'--add-data=../agents/windows_agent.py{separator}.',
        '--hidden-import=win32timezone',
        '../agents/windows_agent.py'
    ])
    
    print("Windows agent built successfully!")
    
    # Build tray application
    PyInstaller.__main__.run([
        '--onefile',
        '--noconsole',
        '--name=syswatch-tray',
        f'--add-data=../agents/version.txt{separator}.',
        '--hidden-import=pystray',
        '--hidden-import=PIL',
        '../agents/windows_tray.py'
    ])
    
    print("Windows tray application built successfully!")
    
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
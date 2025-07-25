import PyInstaller.__main__
import os
import shutil

def build_windows_agent():
    # Build the Windows agent executable
    import sys
    separator = ';' if sys.platform == 'win32' else ':'
    
    PyInstaller.__main__.run([
        '--onefile',
        '--name=nxtclone-agent',
        f'--add-data=../agents/version.txt{separator}.',
        f'--add-data=../agents/agent_updater.py{separator}.',
        '../agents/windows_agent.py'
    ])
    
    print("Windows agent built successfully!")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    build_windows_agent()
import PyInstaller.__main__
import os
import shutil

def build_windows_agent():
    # Build the Windows agent executable
    PyInstaller.__main__.run([
        '--onefile',
        '--noconsole',
        '--name=nxtclone-agent',
        '--add-data=../agents/version.txt;.',
        '--add-data=../agents/agent_updater.py;.',
        '../agents/windows_agent.py'
    ])
    
    print("Windows agent built successfully!")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    build_windows_agent()
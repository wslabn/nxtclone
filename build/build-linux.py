import PyInstaller.__main__
import os

def build_linux_agent():
    # Build the Linux agent executable
    PyInstaller.__main__.run([
        '--onefile',
        '--name=nxtclone-agent',
        '--add-data=../agents/version.txt:.',
        '--add-data=../agents/agent_updater.py:.',
        '../agents/linux_agent.py'
    ])
    
    print("Linux agent built successfully!")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    build_linux_agent()
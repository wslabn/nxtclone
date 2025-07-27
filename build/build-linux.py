import PyInstaller.__main__
import os

def build_linux_agent():
    # Build the Linux agent executable
    import sys
    separator = ';' if sys.platform == 'win32' else ':'
    
    PyInstaller.__main__.run([
        '--onefile',
        '--name=syswatch-agent',
        f'--add-data=../agents/version.txt{separator}.',
        f'--add-data=../agents/agent_updater.py{separator}.',
        '../agents/linux_agent.py'
    ])
    
    print("Linux agent built successfully!")
    
    # Build Linux control application
    PyInstaller.__main__.run([
        '--onefile',
        '--name=syswatch-control',
        f'--add-data=../agents/version.txt{separator}.',
        '../agents/linux_tray.py'
    ])
    
    print("Linux control app built successfully!")
    
    # Create installer
    try:
        import subprocess
        subprocess.run(['chmod', '+x', 'create-linux-installer.sh'], check=True)
        subprocess.run(['./create-linux-installer.sh'], check=True)
        print("Linux installer created successfully!")
    except Exception as e:
        print(f"Warning: Linux installer creation failed: {e}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    build_linux_agent()
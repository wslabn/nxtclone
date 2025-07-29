import PyInstaller.__main__
import os

def build_linux_agent():
    # Read version from package.json and create version file
    import json
    try:
        with open('../package.json', 'r') as f:
            package_data = json.load(f)
            version = package_data.get('version', '1.0.0')
        
        # Create temporary version file for embedding
        with open('temp_version.txt', 'w') as f:
            f.write(version)
        print(f"Version {version} will be embedded in executable")
    except Exception as e:
        print(f"Error reading version: {e}")
        with open('temp_version.txt', 'w') as f:
            f.write('1.0.0')
    
    # Build the Linux agent executable
    import sys
    separator = ';' if sys.platform == 'win32' else ':'
    
    PyInstaller.__main__.run([
        '--onefile',
        '--name=syswatch-agent-linux',
        f'--add-data=temp_version.txt{separator}version.txt',
        f'--add-data=../agents/agent_updater.py{separator}.',
        '../agents/linux_agent.py'
    ])
    
    print("Linux agent built successfully!")
    
    # Build Linux control application
    PyInstaller.__main__.run([
        '--onefile',
        '--name=syswatch-control',
        f'--add-data=temp_version.txt{separator}version.txt',
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
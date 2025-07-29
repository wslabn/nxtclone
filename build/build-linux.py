import PyInstaller.__main__
import os

def build_linux_agent():
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
    
    # Build the Linux agent executable
    import sys
    separator = ';' if sys.platform == 'win32' else ':'
    
    PyInstaller.__main__.run([
        '--onefile',
        '--name=syswatch-agent-linux',
        f'--add-data=../agents/version.py{separator}.',
        f'--add-data=../agents/agent_updater.py{separator}.',
        '../agents/linux_agent.py'
    ])
    
    print("Linux agent built successfully!")
    
    # Build Linux control application
    PyInstaller.__main__.run([
        '--onefile',
        '--name=syswatch-control',
        f'--add-data=../agents/version.py{separator}.',
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
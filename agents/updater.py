#!/usr/bin/env python3
import sys
import os
import time
import subprocess
import shutil
from pathlib import Path

def wait_for_process_exit(process_name, max_wait=30):
    """Wait for process to fully exit"""
    for _ in range(max_wait):
        result = subprocess.run(['tasklist', '/fi', f'imagename eq {process_name}'], 
                              capture_output=True, text=True)
        if process_name not in result.stdout:
            return True
        time.sleep(1)
    return False

def force_kill_process(process_name):
    """Force kill process if still running"""
    subprocess.run(['taskkill', '/f', '/im', process_name], 
                  capture_output=True, check=False)

def stop_service(service_name):
    """Stop Windows service and wait"""
    print(f"Stopping service: {service_name}")
    subprocess.run(['sc', 'stop', service_name], capture_output=True)
    
    # Wait for service to stop
    for _ in range(30):
        result = subprocess.run(['sc', 'query', service_name], 
                              capture_output=True, text=True)
        if 'STOPPED' in result.stdout:
            print("Service stopped successfully")
            return True
        time.sleep(1)
    
    print("Service stop timeout")
    return False

def start_service(service_name):
    """Start Windows service"""
    print(f"Starting service: {service_name}")
    result = subprocess.run(['sc', 'start', service_name], 
                          capture_output=True, text=True)
    return result.returncode == 0

def replace_executable(new_file, target_file):
    """Replace executable with proper error handling"""
    try:
        # Create backup
        backup_file = target_file + ".backup"
        if os.path.exists(target_file):
            shutil.copy2(target_file, backup_file)
            print(f"Created backup: {backup_file}")
        
        # Replace file
        shutil.copy2(new_file, target_file)
        print(f"Replaced: {target_file}")
        
        # Clean up
        os.remove(new_file)
        if os.path.exists(backup_file):
            os.remove(backup_file)
        
        return True
    except Exception as e:
        print(f"File replacement failed: {e}")
        # Restore backup if replacement failed
        if os.path.exists(backup_file) and not os.path.exists(target_file):
            shutil.copy2(backup_file, target_file)
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: updater.py <new_executable> <target_executable>")
        sys.exit(1)
    
    new_exe = sys.argv[1]
    target_exe = sys.argv[2]
    service_name = "SysWatchAgent"
    process_name = "syswatch-agent-windows.exe"
    
    # Ensure temp directory exists
    temp_dir = "C:\\temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        print(f"Created temp directory: {temp_dir}")
    
    print("SysWatch Agent Updater")
    print(f"Updating: {target_exe}")
    print(f"From: {new_exe}")
    
    # Step 1: Stop service
    if not stop_service(service_name):
        print("Failed to stop service, trying force kill...")
    
    # Step 2: Force kill any remaining processes
    force_kill_process(process_name)
    
    # Step 3: Wait for process to fully exit
    print("Waiting for process to exit...")
    if not wait_for_process_exit(process_name):
        print("Warning: Process may still be running")
    
    # Step 4: Additional wait for file handles to release
    time.sleep(3)
    
    # Step 5: Replace executable
    if replace_executable(new_exe, target_exe):
        print("File replacement successful")
    else:
        print("File replacement failed")
        sys.exit(1)
    
    # Step 6: Start service
    if start_service(service_name):
        print("Service started successfully")
        print("Update completed successfully!")
    else:
        print("Failed to start service")
        sys.exit(1)
    
    # Step 7: Clean up updater
    time.sleep(2)
    try:
        # Schedule self-deletion
        batch_script = "C:\\temp\\cleanup.bat"
        with open(batch_script, 'w') as f:
            f.write('@echo off\n')
            f.write('timeout /t 3 /nobreak >nul\n')
            f.write(f'del "{__file__}" >nul 2>&1\n')
            f.write(f'del "{batch_script}" >nul 2>&1\n')
        
        subprocess.Popen([batch_script], shell=True)
    except:
        pass

if __name__ == "__main__":
    main()
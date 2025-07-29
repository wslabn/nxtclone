#!/usr/bin/env python3
import asyncio
import websockets
import json
import socket
import platform
import subprocess
import sys
import os
import psutil
import time
import logging
from agent_updater import AgentUpdater

# Setup logging for service debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('C:\\Windows\\Temp\\syswatch-agent.log'),
        logging.StreamHandler()
    ]
)

class WindowsAgent:
    def __init__(self, server_url="ws://localhost:3000"):
        self.server_url = server_url
        self.client_id = None
        self.hostname = socket.gethostname()
        
        # Initialize CPU measurement for more accurate readings
        psutil.cpu_percent(interval=None)
        # Enhanced Windows version detection with patch level
        if platform.system() == 'Windows':
            try:
                import winreg
                import re
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                current_build = winreg.QueryValueEx(key, "CurrentBuild")[0]
                ubr = winreg.QueryValueEx(key, "UBR")[0]
                
                # Get display version (22H2, 23H2, etc.)
                try:
                    display_version = winreg.QueryValueEx(key, "DisplayVersion")[0]
                except:
                    display_version = winreg.QueryValueEx(key, "ReleaseId")[0]
                
                # Determine Windows version based on build number
                build_num = int(current_build)
                if build_num >= 22000:
                    win_version = "Windows-11"
                else:
                    win_version = "Windows-10"
                
                self.platform = f"{win_version}-{display_version}-{current_build}.{ubr}"
                winreg.CloseKey(key)
            except Exception as e:
                # Fallback to basic detection
                platform_str = platform.platform()
                build_match = re.search(r'10\.0\.(\d+)', platform_str)
                if build_match:
                    build_num = int(build_match.group(1))
                    if build_num >= 22000:
                        self.platform = platform_str.replace('Windows-10', 'Windows-11')
                    else:
                        self.platform = platform_str
                else:
                    self.platform = platform_str
        else:
            self.platform = platform.platform()
        self.updater = AgentUpdater()
        
    async def connect(self):
        # Start periodic update check
        update_task = asyncio.create_task(self.periodic_update_check())
        
        while True:
            try:
                async with websockets.connect(self.server_url) as websocket:
                    print(f"Connected to server: {self.server_url}")
                    
                    # Register with server
                    await self.register(websocket)
                    
                    # Start heartbeat task
                    heartbeat_task = asyncio.create_task(self.heartbeat(websocket))
                    
                    # Listen for messages
                    try:
                        async for message in websocket:
                            await self.handle_message(websocket, json.loads(message))
                    except websockets.exceptions.ConnectionClosed:
                        print("Connection closed by server")
                    finally:
                        heartbeat_task.cancel()
                        
            except Exception as e:
                print(f"Connection failed: {e}")
                print("Retrying in 10 seconds...")
                await asyncio.sleep(10)
    
    async def periodic_update_check(self):
        """Check for updates every 2 hours and auto-update"""
        while True:
            try:
                await asyncio.sleep(2 * 3600)  # 2 hours
                update_info = self.updater.check_for_updates()
                if update_info.get("has_update"):
                    print(f"Auto-update available: {update_info['current_version']} -> {update_info['latest_version']}")
                    if self.updater.download_and_update(update_info["download_url"]):
                        print("Auto-update successful, restarting...")
                        self.updater.restart_agent()
            except Exception as e:
                print(f"Periodic update check failed: {e}")
    
    async def register(self, websocket):
        system_info = self.get_system_info()
        
        # Read version from version.py first, then fallback to package.json
        version = "Unknown"
        try:
            # Try to import version from version.py (embedded in executable)
            try:
                from version import VERSION
                version = VERSION
            except ImportError:
                # Fallback to package.json (for source installs)
                package_file = os.path.join(os.path.dirname(__file__), "..", "package.json")
                if os.path.exists(package_file):
                    with open(package_file, 'r') as f:
                        package_data = json.load(f)
                        version = package_data.get('version', 'Unknown')
        except Exception as e:
            print(f"Could not read version: {e}")
        
        register_msg = {
            "type": "register",
            "hostname": self.hostname,
            "platform": self.platform,
            "system_info": system_info,
            "agentVersion": version
        }
        await websocket.send(json.dumps(register_msg))
        print(f"Registered as {self.hostname} ({self.platform}) - Agent v{version}")
    
    async def heartbeat(self, websocket):
        while True:
            try:
                system_metrics = self.get_system_metrics()
                heartbeat_msg = {
                    "type": "heartbeat",
                    "hostname": self.hostname,
                    "metrics": system_metrics
                }
                await websocket.send(json.dumps(heartbeat_msg))
                await asyncio.sleep(15)  # Send heartbeat every 15 seconds
            except Exception as e:
                print(f"Heartbeat failed: {e}")
                break
    
    async def handle_message(self, websocket, message):
        if message["type"] == "registered":
            self.client_id = message["id"]
            print(f"Assigned client ID: {self.client_id}")
            
        elif message["type"] == "command":
            command_id = message["id"]
            command = message["command"]
            print(f"Executing command: {command}")
            
            try:
                # Handle PowerShell commands directly
                if command.startswith('powershell'):
                    # Extract PowerShell command
                    ps_command = command.replace('powershell ', '').strip('"')
                    result = subprocess.run(
                        ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                else:
                    # Execute regular command with cmd
                    result = subprocess.run(
                        ["cmd", "/c", command],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                
                output = {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
                
            except subprocess.TimeoutExpired:
                output = {"error": "Command timed out"}
            except Exception as e:
                output = {"error": str(e)}
            
            # Send result back
            response = {
                "type": "command_result",
                "id": command_id,
                "hostname": self.hostname,
                "result": output
            }
            await websocket.send(json.dumps(response))
            
        elif message["type"] == "update_request":
            print("Auto-update request received")
            try:
                # Send status update
                await websocket.send(json.dumps({
                    "type": "update_status",
                    "hostname": self.hostname,
                    "status": "checking"
                }))
                
                await websocket.send(json.dumps({
                    "type": "agent_log",
                    "hostname": self.hostname,
                    "message": "Checking for updates..."
                }))
                
                print("Calling updater.check_for_updates()...")
                update_info = self.updater.check_for_updates()
                print(f"Update check result: {update_info}")
                if update_info.get("has_update"):
                    await websocket.send(json.dumps({
                        "type": "update_status",
                        "hostname": self.hostname,
                        "status": "updating",
                        "version": update_info['latest_version'],
                        "currentVersion": update_info['current_version']
                    }))
                    
                    await websocket.send(json.dumps({
                        "type": "agent_log",
                        "hostname": self.hostname,
                        "message": f"Updating from {update_info['current_version']} to {update_info['latest_version']}"
                    }))
                    
                    print(f"Auto-updating: {update_info['current_version']} -> {update_info['latest_version']}")
                    if self.updater.download_and_update(update_info["download_url"]):
                        await websocket.send(json.dumps({
                            "type": "agent_log",
                            "hostname": self.hostname,
                            "message": "Update successful, restarting agent..."
                        }))
                        print("Update successful, restarting...")
                        self.updater.restart_agent()
                    else:
                        await websocket.send(json.dumps({
                            "type": "agent_log",
                            "hostname": self.hostname,
                            "message": "Update download/install failed"
                        }))
                else:
                    await websocket.send(json.dumps({
                        "type": "update_status",
                        "hostname": self.hostname,
                        "status": "up_to_date"
                    }))
                    
                    await websocket.send(json.dumps({
                        "type": "agent_log",
                        "hostname": self.hostname,
                        "message": "Agent is already up to date"
                    }))
                    print("Agent is already up to date")
            except Exception as e:
                print(f"Update request handler error: {e}")
                try:
                    await websocket.send(json.dumps({
                        "type": "update_status",
                        "hostname": self.hostname,
                        "status": "error",
                        "error": str(e)
                    }))
                    
                    await websocket.send(json.dumps({
                        "type": "agent_log",
                        "hostname": self.hostname,
                        "message": f"Update failed: {str(e)}"
                    }))
                except:
                    pass
                print(f"Auto-update failed: {e}")
                
        elif message["type"] == "uninstall_request":
            print("Uninstall request received")
            try:
                await websocket.send(json.dumps({
                    "type": "agent_log",
                    "hostname": self.hostname,
                    "message": "Starting agent uninstall..."
                }))
                
                # Uninstall commands for Windows
                uninstall_commands = [
                    'sc stop "SysWatch Agent"',
                    'sc delete "SysWatch Agent"',
                    'rmdir /s /q "C:\\Program Files\\SysWatch"',
                    'rmdir /s /q "C:\\Program Files (x86)\\SysWatch"'
                ]
                
                for cmd in uninstall_commands:
                    print(f"Executing: {cmd}")
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode != 0 and "rmdir" not in cmd:
                        print(f"Warning: {cmd} failed: {result.stderr}")
                
                await websocket.send(json.dumps({
                    "type": "agent_log",
                    "hostname": self.hostname,
                    "message": "Agent uninstalled successfully. Goodbye!"
                }))
                
                print("Agent uninstalled. Exiting...")
                sys.exit(0)
                
            except Exception as e:
                await websocket.send(json.dumps({
                    "type": "agent_log",
                    "hostname": self.hostname,
                    "message": f"Uninstall failed: {str(e)}"
                }))
                print(f"Uninstall failed: {e}")
                
        elif message["type"] == "config_update":
            print("Configuration update received")
            try:
                config = message.get("config", {})
                for key, value in config.items():
                    await self.apply_config(key, value)
                    
                    # Acknowledge configuration applied
                    await websocket.send(json.dumps({
                        "type": "config_applied",
                        "hostname": self.hostname,
                        "configKey": key
                    }))
            except Exception as e:
                print(f"Config update failed: {e}")
    
    async def apply_config(self, key, value):
        """Apply configuration setting"""
        try:
            if key == "heartbeat_interval":
                # Update heartbeat interval (would need to restart heartbeat task)
                print(f"Heartbeat interval updated to {value} seconds")
            elif key == "server_url":
                # Update server URL (would need reconnection)
                print(f"Server URL updated to {value}")
            elif key == "log_level":
                # Update logging level
                print(f"Log level updated to {value}")
            else:
                print(f"Unknown config key: {key}")
        except Exception as e:
            print(f"Failed to apply config {key}: {e}")
    
    def get_system_info(self):
        """Get static system information"""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                "memory_total": psutil.virtual_memory().total,
                "disk_total": psutil.disk_usage('C:\\').total,
                "boot_time": psutil.boot_time(),
                "platform_details": platform.platform(),
                "architecture": platform.architecture()[0]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_system_metrics(self):
        """Get real-time system metrics with improved accuracy"""
        try:
            # Take multiple CPU samples for better accuracy
            cpu_samples = []
            for _ in range(3):
                cpu_samples.append(psutil.cpu_percent(interval=0.5))
            
            # Use median to avoid spikes
            cpu_percent = sorted(cpu_samples)[1]
            
            # Get memory and disk info
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('C:\\')
            
            # Force refresh memory stats
            memory = psutil.virtual_memory()
            
            return {
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "memory_used": memory.used,
                "disk_percent": round((disk.used / disk.total) * 100, 1),
                "disk_used": disk.used,
                "process_count": len(psutil.pids()),
                "network_io": dict(psutil.net_io_counters()._asdict()) if psutil.net_io_counters() else {},
                "timestamp": time.time()
            }
        except Exception as e:
            return {"error": str(e)}

def main():
    """Main function for both service and console execution"""
    server_url = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:3000"
    agent = WindowsAgent(server_url)
    
    logging.info(f"Starting Windows Agent for {agent.hostname}")
    logging.info(f"Connecting to: {server_url}")
    logging.info("Auto-update enabled - agent will update automatically")
    
    # Handle Windows service signals
    import signal
    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        asyncio.run(agent.connect())
    except KeyboardInterrupt:
        logging.info("Agent stopped by user")
    except Exception as e:
        logging.error(f"Agent error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if running as Windows service
    if len(sys.argv) > 1 and sys.argv[1] in ['install', 'remove', 'start', 'stop', 'restart']:
        # Service management commands - ignore for now
        print(f"Service command '{sys.argv[1]}' - use Windows Service Manager instead")
        sys.exit(0)
    else:
        # Normal execution
        main()
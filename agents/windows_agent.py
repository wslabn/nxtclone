import asyncio
import websockets
import json
import socket
import platform
import subprocess
import sys
import time
import psutil
import os
from agent_updater import AgentUpdater

class WindowsAgent:
    def __init__(self, server_url="ws://localhost:3000"):
        self.server_url = server_url
        self.client_id = None
        self.hostname = socket.gethostname()
        self.platform = f"{platform.system()} {platform.release()}"
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
        register_msg = {
            "type": "register",
            "hostname": self.hostname,
            "platform": self.platform,
            "system_info": system_info
        }
        await websocket.send(json.dumps(register_msg))
        print(f"Registered as {self.hostname} ({self.platform})")
    
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
                # Execute command
                result = subprocess.run(
                    command,
                    shell=True,
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
                update_info = self.updater.check_for_updates()
                if update_info.get("has_update"):
                    print(f"Auto-updating: {update_info['current_version']} -> {update_info['latest_version']}")
                    if self.updater.download_and_update(update_info["download_url"]):
                        print("Update successful, restarting...")
                        self.updater.restart_agent()
                else:
                    print("Agent is already up to date")
            except Exception as e:
                print(f"Auto-update failed: {e}")
    
    def get_system_info(self):
        """Get static system information"""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                "memory_total": psutil.virtual_memory().total,
                "disk_total": psutil.disk_usage('/').total if os.name != 'nt' else psutil.disk_usage('C:').total,
                "boot_time": psutil.boot_time(),
                "platform_details": platform.platform(),
                "architecture": platform.architecture()[0]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_system_metrics(self):
        """Get real-time system metrics"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('C:') if os.name == 'nt' else psutil.disk_usage('/')
            
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": memory.percent,
                "memory_used": memory.used,
                "disk_percent": (disk.used / disk.total) * 100,
                "disk_used": disk.used,
                "process_count": len(psutil.pids()),
                "network_io": dict(psutil.net_io_counters()._asdict()) if psutil.net_io_counters() else {},
                "timestamp": time.time()
            }
        except Exception as e:
            return {"error": str(e)}

def install_service(server_url):
    """Install as Windows service"""
    import subprocess
    import sys
    
    service_name = "NxtClone Agent"
    exe_path = sys.executable if sys.executable.endswith('.exe') else sys.argv[0]
    
    # Create service
    cmd = f'sc create "{service_name}" binPath= "\"{exe_path}\" {server_url}" start= auto'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"Service '{service_name}' installed successfully")
        print(f"Server URL: {server_url}")
        print("Starting service...")
        subprocess.run(f'sc start "{service_name}"', shell=True)
    else:
        print(f"Failed to install service: {result.stderr}")

def uninstall_service():
    """Uninstall Windows service"""
    import subprocess
    
    service_name = "NxtClone Agent"
    
    # Stop and delete service
    subprocess.run(f'sc stop "{service_name}"', shell=True)
    result = subprocess.run(f'sc delete "{service_name}"', shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"Service '{service_name}' uninstalled successfully")
    else:
        print(f"Failed to uninstall service: {result.stderr}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "install":
            server_url = sys.argv[2] if len(sys.argv) > 2 else "ws://localhost:3000"
            install_service(server_url)
            sys.exit(0)
        elif sys.argv[1] == "uninstall":
            uninstall_service()
            sys.exit(0)
        elif sys.argv[1].startswith("ws://"):
            server_url = sys.argv[1]
        else:
            print("Usage:")
            print("  nxtclone-agent.exe install [server_url]  - Install as service")
            print("  nxtclone-agent.exe uninstall             - Remove service")
            print("  nxtclone-agent.exe ws://server:port      - Run directly")
            sys.exit(1)
    else:
        server_url = "ws://localhost:3000"
    
    agent = WindowsAgent(server_url)
    
    print(f"Starting Windows Agent for {agent.hostname}")
    print(f"Connecting to: {server_url}")
    print("Auto-update enabled - agent will update automatically")
    
    asyncio.run(agent.connect())
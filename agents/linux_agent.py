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
from agent_updater import AgentUpdater

class LinuxAgent:
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
                # Check for manual update trigger file
                if os.path.exists('/tmp/syswatch-update-now'):
                    os.remove('/tmp/syswatch-update-now')
                    print("Manual update trigger detected")
                    update_info = self.updater.check_for_updates()
                    if update_info.get("has_update"):
                        print(f"Manual update: {update_info['current_version']} -> {update_info['latest_version']}")
                        if self.updater.download_and_update(update_info["download_url"]):
                            print("Manual update successful, restarting...")
                            self.updater.restart_agent()
                
                await asyncio.sleep(30)  # Check every 30 seconds for trigger file
                
                # Regular 2-hour update check
                await asyncio.sleep(2 * 3600 - 30)  # 2 hours minus the 30 seconds above
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
                # Execute command with bash
                result = subprocess.run(
                    ["/bin/bash", "-c", command],
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
                
                update_info = self.updater.check_for_updates()
                if update_info.get("has_update"):
                    await websocket.send(json.dumps({
                        "type": "update_status",
                        "hostname": self.hostname,
                        "status": "updating",
                        "version": update_info['latest_version']
                    }))
                    
                    print(f"Auto-updating: {update_info['current_version']} -> {update_info['latest_version']}")
                    if self.updater.download_and_update(update_info["download_url"]):
                        print("Update successful, restarting...")
                        self.updater.restart_agent()
                else:
                    await websocket.send(json.dumps({
                        "type": "update_status",
                        "hostname": self.hostname,
                        "status": "up_to_date"
                    }))
                    print("Agent is already up to date")
            except Exception as e:
                await websocket.send(json.dumps({
                    "type": "update_status",
                    "hostname": self.hostname,
                    "status": "error",
                    "error": str(e)
                }))
                print(f"Auto-update failed: {e}")
    
    def get_system_info(self):
        """Get static system information"""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                "memory_total": psutil.virtual_memory().total,
                "disk_total": psutil.disk_usage('/').total,
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
            disk = psutil.disk_usage('/')
            
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

if __name__ == "__main__":
    server_url = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:3000"
    agent = LinuxAgent(server_url)
    
    print(f"Starting Linux Agent for {agent.hostname}")
    print(f"Connecting to: {server_url}")
    print("Auto-update enabled - agent will update automatically")
    
    asyncio.run(agent.connect())
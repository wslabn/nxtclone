# SysWatch - Remote Monitoring & Management

A lightweight RMM system for monitoring machine connectivity, executing remote commands, and providing comprehensive system insights.

## Features

- **Real-time System Monitoring**: CPU, memory, disk usage with live metrics
- **Cross-platform Agents**: Windows, Linux, macOS, ChromeOS support
- **Remote Command Execution**: Execute commands on any connected machine
- **Automatic Updates**: Fully automated update system via GitHub releases
- **Web Dashboard**: Modern interface with system information display
- **System Tray Control**: Windows tray icon and Linux control app
- **Scalable UI**: Card and table views for 100+ machines
- **Offline Detection**: Real-time alerts when machines disconnect
- **System Information**: Hardware specs, uptime, process counts
- **Enterprise-grade**: Built for scalability and reliability

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/wslabn/nxtclone.git
cd nxtclone
```

### 2. Install Server Dependencies
```bash
npm install
```

### 3. Start Server
```bash
npm start
```
Server runs on http://localhost:3000

### 4. Install Agents

**Option A - Download Executables (Recommended):**
- Download `syswatch-agent-installer.exe` (Windows) or `syswatch-agent-installer-linux` (Linux) from [Releases](https://github.com/wslabn/nxtclone/releases)
- Windows: Run installer as administrator
- Linux: `sudo ./syswatch-agent-installer-linux ws://your-server:3000`

**Option B - Run from Source:**
```bash
cd agents
pip install -r requirements.txt

# Windows
python windows_agent.py

# Linux  
python3 linux_agent.py

# Custom server URL
python windows_agent.py ws://your-server:3000
```

## Usage

1. **Dashboard Access**: Open http://localhost:3000 in your browser
2. **Deploy Agents**: Install executables or run from source on target machines
3. **Monitor Systems**: View real-time metrics, system info, and status
4. **Execute Commands**: Send commands remotely via web interface
5. **Auto-Updates**: System automatically updates from GitHub releases
6. **Offline Monitoring**: Get alerts when machines disconnect

## Agent Installation

**Windows Service Installation:**
1. Download `syswatch-agent-installer.exe` from releases
2. Run as administrator
3. Enter server URL when prompted (e.g., `ws://192.168.1.100:3000`)
4. Agent installs as Windows service and starts automatically
5. Optional: Run `syswatch-tray.exe` for system tray control

**Linux Service Installation:**
1. Download `syswatch-agent-installer-linux` from releases
2. Run: `sudo ./syswatch-agent-installer-linux ws://192.168.1.100:3000`
3. Agent installs as systemd service and starts automatically
4. Optional: Run `./syswatch-control` for GUI/CLI management

**Manual Execution:**
- Windows: `syswatch-agent.exe`
- Linux: `./syswatch-agent`

## Architecture

- **Server**: Node.js WebSocket server with Express web interface
- **Agents**: Python asyncio-based clients with heartbeat and system monitoring
- **Database**: SQLite for storing machine info, system data, and command history
- **Communication**: WebSocket for real-time bidirectional messaging
- **Auto-Update**: GitHub API integration for automatic updates
- **System Monitoring**: psutil-based comprehensive system metrics collection

## System Information Collected

- **Hardware**: CPU cores, memory, disk space, architecture
- **Performance**: Real-time CPU, memory, disk usage percentages
- **System**: Platform details, uptime, boot time
- **Processes**: Active process count and management
- **Network**: I/O statistics and connectivity status
- **Software**: Installed programs and agent version information

## Command Examples

- **Windows**: `dir`, `systeminfo`, `tasklist`, `wmic cpu get name`
- **Linux**: `ls -la`, `ps aux`, `df -h`, `uname -a`, `top -n1`

## Quick Action Buttons

- **Shutdown/Reboot**: Safe system restart with confirmation
- **Processes**: View running processes and resource usage
- **Services**: List system services and their status
- **Network**: Display network configuration and connections
- **Software**: Show installed software and agent version

## Auto-Update System

- **Automatic Detection**: Agents check GitHub releases every 2 hours
- **Manual Updates**: "Update All Agents" button for immediate updates
- **Zero-Touch Updates**: Agents update automatically without intervention
- **Real-time Progress**: Dashboard shows update status and progress
- **Service Integration**: Windows services and Linux systemd units restart automatically
- **Version Management**: Synchronized versioning across all components
- **Enterprise Ready**: GitHub Actions for automated release management
- **Local Triggers**: Force updates locally via service restart or trigger files

## Building Executables

**Windows:**
```bash
cd build
build-all.bat
```

**Linux:**
```bash
cd build
chmod +x build-all.sh
./build-all.sh
```

**Requirements:**
- Python 3.9+
- PyInstaller
- NSIS (Windows installer creation)

## Security Notes

This is a basic implementation. For production use, add:
- Authentication/authorization
<<<<<<< HEAD
- TLS encryption (WSS://)
- Command validation and sandboxing
- Rate limiting and DDoS protection
- Comprehensive audit logging
- Network segmentation
- Agent certificate validation

## Releases

Create releases via GitHub Actions:
1. Go to Actions → "Manual Release"
2. Click "Run workflow"
3. Enter version (e.g., "1.0.1")
4. Automatically builds executables and creates release

## Troubleshooting

For common issues and solutions, see the [Troubleshooting Guide](TROUBLESHOOTING.md).

**Quick Help:**
- Agent not connecting: Check service status and logs
- Auto-update failing: Verify GitHub connectivity and agent version
- Dashboard issues: Clear browser cache, check authentication
- Command execution problems: Verify agent permissions and syntax

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## License

MIT License - see LICENSE file for details

## Dashboard Features

- **Real-time Monitoring**: Live system metrics with progress bars
- **Scalable Views**: Card view for details, table view for 100+ machines
- **Machine Management**: Online/offline status with cleanup tools
- **Remote Commands**: Execute commands with modal result display
- **Update Management**: Check for updates and monitor progress
- **Quick Actions**: Pre-configured system management buttons
- **Software Inventory**: View installed programs and versions
- **System Tray Control**: Windows tray icon and Linux control app

## Documentation

- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions
- **[Installation Guide](#agent-installation)** - Step-by-step setup instructions
- **[API Documentation](#command-examples)** - Command examples and usage

## System Tray Control

**Windows:**
- Run `syswatch-tray.exe` for system tray icon
- Right-click menu: Change server, restart service, view logs, about
- Persistent configuration storage

**Linux:**
- Run `./syswatch-control` for GUI (if available) or CLI interface
- Auto-detects GUI availability, falls back to terminal menu
- Same features: server config, service control, log viewing

## Project Stats
- Total Code Files: 15
- Last Updated: 2025-01-25
- Current Version: 1.2.9

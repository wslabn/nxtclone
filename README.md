# SysWatch - Remote Monitoring & Management

A lightweight RMM system for monitoring machine connectivity, executing remote commands, and providing comprehensive system insights.

## Features

- **Real-time System Monitoring**: CPU, memory, disk usage with live metrics
- **Cross-platform Agents**: Windows, Linux, macOS, ChromeOS support
- **Remote Command Execution**: Execute commands on any connected machine
- **Automatic Updates**: Fully automated update system via GitHub releases
- **Web Dashboard**: Modern interface with system information display
- **Optional Control Apps**: Windows tray icon and Linux control app
- **Scalable UI**: Card and table views for 100+ machines
- **Offline Detection**: Real-time alerts when machines disconnect
- **System Information**: Hardware specs, uptime, process counts
- **Discord Alerts**: Notifications for offline machines, high usage, and uninstalls
- **Agent Uninstall**: Remote uninstall capability via dashboard

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

**Windows:**
```cmd
# Download and run installer
https://github.com/wslabn/nxtclone/releases/latest/download/syswatch-agent-installer.exe
```
1. Run as administrator
2. Enter server URL (e.g., `ws://192.168.1.100:3000`)
3. Choose whether to install system tray control app
4. Agent installs as Windows service and starts automatically

**Linux:**
```bash
# Download installer
wget https://github.com/wslabn/nxtclone/releases/latest/download/syswatch-agent-installer-linux
chmod +x syswatch-agent-installer-linux

# Install with your server URL
sudo ./syswatch-agent-installer-linux ws://192.168.1.100:3000
```
1. Choose whether to install control application
2. Agent installs as systemd service and starts automatically

**Manual Execution (Development):**
```bash
cd agents
pip install -r requirements.txt

# Windows
python windows_agent.py ws://your-server:3000

# Linux  
python3 linux_agent.py ws://your-server:3000
```

## Usage

1. **Dashboard Access**: Open http://localhost:3000 in your browser
2. **Deploy Agents**: Install using the installers on target machines
3. **Monitor Systems**: View real-time metrics, system info, and status
4. **Execute Commands**: Send commands remotely via web interface
5. **Auto-Updates**: System automatically updates from GitHub releases
6. **Offline Monitoring**: Get alerts when machines disconnect
7. **Remote Uninstall**: Uninstall agents remotely via dashboard

## Control Applications

**Windows Tray App:**
- Optional installation during agent setup
- System tray icon with right-click menu
- Change server URL, restart service, view logs
- Desktop shortcut created if installed

**Linux Control App:**
- Optional installation during agent setup
- Available system-wide as `syswatch-control`
- GUI (if available) or CLI interface
- Manage service, view logs, change configuration

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
- **Uninstall**: Remove agent from remote machine

## Auto-Update System

- **Automatic Detection**: Agents check GitHub releases every 2 hours
- **Manual Updates**: "Update All Agents" button for immediate updates
- **Zero-Touch Updates**: Agents update automatically without intervention
- **Real-time Progress**: Dashboard shows update status and progress
- **Service Integration**: Windows services and Linux systemd units restart automatically
- **Version Management**: Synchronized versioning across all components
- **Control App Updates**: Tray and control apps update automatically with agent
- **Enterprise Ready**: GitHub Actions for automated release management

## Discord Notifications

Configure Discord webhook in admin panel for alerts:
- **Machine Offline**: When agents disconnect
- **Machine Online**: When agents reconnect
- **High Resource Usage**: CPU/Memory/Disk above 89%
- **Agent Uninstalled**: When agents are removed remotely

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
3. Enter version (e.g., "1.2.11")
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
- **Remote Uninstall**: Remove agents from dashboard
- **Discord Integration**: Real-time notifications and alerts

## Project Stats
- Total Code Files: 15
- Last Updated: 2025-01-25
- Current Version: 1.2.12
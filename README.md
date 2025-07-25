# NxtClone - Remote Monitoring & Management

A lightweight RMM system for monitoring machine connectivity, executing remote commands, and providing comprehensive system insights similar to Nexthink.

## Features

- **Real-time System Monitoring**: CPU, memory, disk usage with live metrics
- **Cross-platform Agents**: Windows, Linux, macOS, ChromeOS support
- **Remote Command Execution**: Execute commands on any connected machine
- **Automatic Updates**: Fully automated update system via GitHub releases
- **Web Dashboard**: Modern interface with system information display
- **Offline Detection**: Real-time alerts when machines disconnect
- **System Information**: Hardware specs, uptime, process counts
- **Enterprise-grade**: Built for scalability and reliability

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/YOUR-USERNAME/nxtclone.git
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
- Download `nxtclone-agent-windows.exe` or `nxtclone-agent-linux` from [Releases](https://github.com/YOUR-USERNAME/nxtclone/releases)
- Windows: Run installer or executable directly
- Linux: `chmod +x nxtclone-agent-linux && ./nxtclone-agent-linux`

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
1. Download `nxtclone-agent-installer.exe` from releases
2. Run as administrator
3. Agent installs as Windows service and starts automatically

**Linux Service Installation:**
1. Download `nxtclone-agent-linux` and `install-linux.sh`
2. Run: `sudo ./install-linux.sh`
3. Agent installs as systemd service and starts automatically

**Manual Execution:**
- Windows: `nxtclone-agent-windows.exe`
- Linux: `./nxtclone-agent-linux`

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

## Command Examples

- **Windows**: `dir`, `systeminfo`, `tasklist`, `wmic cpu get name`
- **Linux**: `ls -la`, `ps aux`, `df -h`, `uname -a`, `top -n1`

## Auto-Update System

- **Automatic Detection**: Server checks GitHub releases every 30 minutes
- **Zero-Touch Updates**: Agents update automatically without intervention
- **Executable Updates**: Both source and compiled agents update seamlessly
- **Service Integration**: Windows services and Linux systemd units restart automatically
- **Version Management**: Synchronized versioning across all components
- **Enterprise Ready**: GitHub Actions for automated release management

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

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## License

MIT License - see LICENSE file for details
=======
- TLS encryption
- Command validation
- Rate limiting
- Audit logging
## Project Stats
- Total Code Files: 6
- Last Updated: 2025-07-25
>>>>>>> 377f45da1f1a00d29401f5a16cd2764b4bcd56ec

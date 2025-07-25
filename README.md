# NxtClone - Remote Monitoring & Management

A lightweight RMM system for monitoring machine connectivity and executing remote commands.

## Features

- Real-time connectivity monitoring
- Remote command execution
- Cross-platform agents (Windows, Linux)
- Web-based dashboard
- Offline detection and alerts

## Quick Start

### 1. Install Server Dependencies
```bash
npm install
```

### 2. Start Server
```bash
npm start
```
Server runs on http://localhost:3000

### 3. Install Agent Dependencies
```bash
cd agents
pip install -r requirements.txt
```

### 4. Run Agents

**Windows:**
```bash
python windows_agent.py
```

**Linux:**
```bash
python3 linux_agent.py
```

**Custom server URL:**
```bash
python windows_agent.py ws://your-server:3000
```

## Usage

1. Open http://localhost:3000 in your browser
2. Start agents on target machines
3. View connected machines in dashboard
4. Execute commands remotely
5. Monitor for offline alerts in server console

## Architecture

- **Server**: Node.js WebSocket server with Express web interface
- **Agents**: Python asyncio-based clients with heartbeat mechanism
- **Database**: SQLite for storing machine info and command history
- **Communication**: WebSocket for real-time bidirectional messaging

## Command Examples

- Windows: `dir`, `systeminfo`, `tasklist`
- Linux: `ls -la`, `ps aux`, `df -h`, `uname -a`

## Security Notes

This is a basic implementation. For production use, add:
- Authentication/authorization
- TLS encryption
- Command validation
- Rate limiting
- Audit logging
## Project Stats
- Total Code Files: 6
- Last Updated: 2025-07-25

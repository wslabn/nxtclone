# SysWatch Troubleshooting Guide

## Installation Issues

### Windows Installer

**Error 1053 - Service won't start:**
```
Solution: Fixed in v1.2.12+ - installer now uses correct paths
For older versions: Check service path with 'sc qc "SysWatch Agent"'
Manual fix: sc delete "SysWatch Agent" && sc create "SysWatch Agent" binPath="\"C:\Program Files\SysWatch\syswatch-agent-windows.exe\" ws://server:3000" start=auto
```

**Installer fails to run:**
```
Solution: Right-click installer → "Run as administrator"
Check: Windows Defender/antivirus isn't blocking
```

**Service installed but not connecting:**
```
Check: Service is actually running - sc query "SysWatch Agent"
Verify: Server URL format is correct (ws://server:3000)
Test: Manual execution: "C:\Program Files\SysWatch\syswatch-agent-windows.exe" ws://server:3000
Firewall: Ensure outbound connections on port 3000 allowed
```

### Linux Installer

**Permission denied:**
```bash
sudo chmod +x syswatch-agent-installer-linux
sudo ./syswatch-agent-installer-linux ws://server:3000
```

**Service fails to start:**
```bash
# Check service status
sudo systemctl status syswatch-agent

# View logs
sudo journalctl -u syswatch-agent -f

# Manual test
sudo -u syswatch /opt/syswatch/syswatch-agent-linux ws://server:3000
```

**Control app not found after installation:**
```bash
# Check if symlink exists
ls -la /usr/local/bin/syswatch-control

# Manual execution
/opt/syswatch/syswatch-control
```

## Connection Issues

### Agent Not Connecting

**Check server URL format:**
```
Correct: ws://192.168.1.100:3000
Incorrect: http://192.168.1.100:3000
Incorrect: 192.168.1.100:3000
```

**Firewall blocking connection:**
```bash
# Windows: Allow outbound on port 3000
# Linux: Check iptables/ufw rules
sudo ufw allow out 3000
```

**Server not running:**
```bash
# Start server
cd /path/to/syswatch
npm start

# Check if port is open
netstat -an | grep :3000
```

### Agent Shows Offline

**Check heartbeat timing:**
- Agents send heartbeat every 15 seconds
- Server marks offline after 30 seconds
- Network delays can cause false offline status

**Service stopped:**
```bash
# Windows
sc query "SysWatch Agent"
sc start "SysWatch Agent"

# Linux
sudo systemctl status syswatch-agent
sudo systemctl start syswatch-agent
```

## Auto-Update Issues

### Updates Not Working

**Check GitHub connectivity:**
```bash
# Test from agent machine
curl -I https://api.github.com/repos/wslabn/nxtclone/releases/latest
```

**Agent version too old:**
- Agents before v1.2.8 may have update issues
- Manually reinstall with latest installer

**Service permissions:**
```bash
# Windows: Service must run as SYSTEM or admin
# Linux: Service runs as syswatch user with proper permissions
```

### Update Fails Mid-Process

**Windows:**
```cmd
# Stop service
sc stop "SysWatch Agent"

# Check for .old/.new files in install directory
dir "C:\Program Files\SysWatch"

# Restart service
sc start "SysWatch Agent"
```

**Linux:**
```bash
# Stop service
sudo systemctl stop syswatch-agent

# Check for backup files
ls -la /opt/syswatch/

# Restart service
sudo systemctl start syswatch-agent
```

## Dashboard Issues

### Can't Access Dashboard

**Server not running:**
```bash
npm start
# Should show: RMM Server running on port 3000
```

**Wrong URL:**
```
Correct: http://localhost:3000
Check: Server IP if accessing remotely
```

**Authentication issues:**
```
Default login: admin/admin
Reset: Delete server/users.json and restart server
```

### Machines Not Showing

**Check agent logs:**
```bash
# Windows
# Check Windows Event Viewer or service logs

# Linux
sudo journalctl -u syswatch-agent -f
```

**Database issues:**
```bash
# Delete database to reset
rm server/rmm.db
# Restart server - will recreate database
```

## Command Execution Issues

### Commands Fail to Execute

**Permission issues:**
```
Windows: Service runs as SYSTEM - has admin rights
Linux: Service runs as syswatch user - limited permissions
```

**Command syntax:**
```bash
# Windows: Use cmd syntax
dir C:\
systeminfo

# Linux: Use bash syntax
ls -la /
ps aux
```

**Timeout issues:**
- Commands timeout after 30 seconds
- Use shorter commands or background execution

### No Command Results

**Check agent connection:**
- Agent must be online to receive commands
- Check WebSocket connection status

**Result retrieval:**
- Results stored temporarily in server memory
- Refresh page if results don't appear

## Control App Issues

### Windows Tray App

**Tray icon not appearing:**
```
Location: C:\Program Files\SysWatch\syswatch-tray.exe (if installed)
Check: Windows notification area settings
Manual run: Right-click → "Run as administrator"
Restart: Windows Explorer process if needed
```

**Tray app logs not opening:**
```
Solution: Tray opens Windows Event Viewer (correct behavior)
Logs location: Event Viewer → Windows Logs → Application
Filter by: Source = "SysWatch Agent"
Note: Service must be running to generate logs
```

**Can't change server URL:**
```
Run tray as administrator for service control
Config saved to: tray_config.json in install directory
```

### Linux Control App

**Command not found:**
```bash
# Check symlink
ls -la /usr/local/bin/syswatch-control

# Run directly
/opt/syswatch/syswatch-control
```

**GUI not working:**
```bash
# Check if GUI libraries available
python3 -c "import tkinter"

# Falls back to CLI if GUI unavailable
```

## Discord Notifications

### Alerts Not Sending

**Webhook URL incorrect:**
```
Check: Discord webhook URL format
Test: Send test message from admin panel
```

**Network connectivity:**
```bash
# Test from server
curl -X POST [webhook-url] -H "Content-Type: application/json" -d '{"content":"test"}'
```

**Rate limiting:**
- Discord has rate limits on webhooks
- Server respects limits automatically

## Performance Issues

### High Resource Usage

**Server performance:**
```bash
# Check server resources
top
htop

# Reduce update frequency if needed
# Edit heartbeat interval in agent code
```

**Agent performance:**
```bash
# Check agent resource usage
ps aux | grep syswatch
```

**Database size:**
```bash
# Check database size
ls -lh server/rmm.db

# Clean old data (automatic after 7 days)
```

## Uninstall Issues

### Remote Uninstall Fails

**Agent doesn't support uninstall:**
- Feature added in v1.2.8+
- Older agents need manual uninstall

**Permission issues:**
```bash
# Windows: Service needs admin rights
# Linux: Service needs sudo access for uninstall
```

### Manual Uninstall

**Windows:**
```cmd
sc stop "SysWatch Agent"
sc delete "SysWatch Agent"
rmdir /s /q "C:\Program Files\SysWatch"
```

**Linux:**
```bash
sudo systemctl stop syswatch-agent
sudo systemctl disable syswatch-agent
sudo rm -f /etc/systemd/system/syswatch-agent.service
sudo systemctl daemon-reload
sudo rm -rf /opt/syswatch
sudo rm -f /usr/local/bin/syswatch-control
sudo userdel syswatch
```

## Log Locations

**Server logs:**
- Console output when running `npm start`
- Admin panel → Logs section

**Windows agent logs:**
- Windows Event Viewer → Application logs
- Filter by Source: "SysWatch Agent"
- Tray app "View Logs" opens Event Viewer automatically
- Service start/stop events in System logs

**Linux agent logs:**
```bash
sudo journalctl -u syswatch-agent -f
sudo journalctl -u syswatch-agent --since "1 hour ago"
```

## Getting Help

1. **Check logs first** - Most issues show in logs
2. **Test connectivity** - Ensure network access
3. **Verify versions** - Use latest releases
4. **Manual testing** - Run agents manually to debug
5. **GitHub Issues** - Report bugs with logs

## Common Error Codes

- **1053**: Windows service executable not found
- **1077**: Windows service path invalid
- **Connection refused**: Server not running or firewall blocking
- **404**: Update URL incorrect or release not found
- **Timeout**: Network connectivity issues
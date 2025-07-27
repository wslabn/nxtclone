# SysWatch Troubleshooting Guide

## Agent Connection Issues

### Check Agent Status

**Linux:**
```bash
# Check service status
systemctl status syswatch-agent

# View recent logs
journalctl -u syswatch-agent -n 50

# Follow logs in real-time
journalctl -u syswatch-agent -f

# Check if agent is running
ps aux | grep syswatch

# Use control application
./syswatch-control
```

**Windows:**
```cmd
# Check service status
sc query "SysWatch Agent"

# View service details
sc queryex "SysWatch Agent"

# Check running processes
tasklist | findstr syswatch

# Use tray application
syswatch-tray.exe
```

### Agent Not Connecting

1. **Check server URL in agent configuration**
2. **Verify network connectivity:**
   ```bash
   # Test connection to server
   telnet your-server-ip 3000
   # or
   nc -zv your-server-ip 3000
   ```
3. **Check firewall settings** - Port 3000 must be open
4. **Restart agent service:**
   - Linux: `sudo systemctl restart syswatch-agent` or use `./syswatch-control`
   - Windows: `sc stop "SysWatch Agent" && sc start "SysWatch Agent"` or use tray app

## Auto-Update Issues

### Check Agent Version

**Linux:**
```bash
cat /opt/syswatch/version.txt
# or use control app
./syswatch-control
```

**Windows:**
```cmd
type "C:\Program Files\SysWatch\SysWatch Agent\version.txt"
# or use tray app
syswatch-tray.exe
```

### Update Troubleshooting

1. **Check GitHub connectivity:**
   ```bash
   curl -I https://api.github.com/repos/wslabn/nxtclone/releases/latest
   ```

2. **Manual update trigger (Linux):**
   ```bash
   sudo touch /tmp/syswatch-update-now
   ```

3. **View update logs:**
   - **Server:** Admin Panel → View Update Logs
   - **Linux:** `journalctl -u syswatch-agent -f` or `./syswatch-control`
   - **Windows:** Event Viewer → Application → SysWatch Agent or tray app

4. **Force agent reinstall if updates fail:**
   - Download latest release from GitHub
   - Reinstall agent with new executable

## Dashboard Issues

### Authentication Problems

1. **Reset admin password:**
   ```bash
   # Delete auth database and restart server
   rm server/auth.db
   npm start
   # Default: admin/admin
   ```

2. **Clear browser cache** - Hard refresh (Ctrl+F5)

3. **Check session cookies** - Clear site data in browser

### Machines Not Appearing

1. **Check agent logs** for connection errors
2. **Verify server is running** on correct port
3. **Check database:**
   ```bash
   # View machines table
   sqlite3 server/database.db "SELECT * FROM machines;"
   ```

## Performance Issues

### High Resource Usage

1. **Check metrics collection interval** (default: 15 seconds)
2. **Database cleanup:**
   ```bash
   # Clean old metrics (keeps 7 days)
   sqlite3 server/database.db "DELETE FROM metrics WHERE timestamp < strftime('%s', 'now', '-7 days') * 1000;"
   ```

3. **Restart server** to clear memory leaks

### Slow Dashboard Loading

1. **Check network latency** between browser and server
2. **Reduce update frequency** in dashboard (default: 10 seconds)
3. **Clear browser cache**

## Command Execution Issues

### Commands Timing Out

1. **Increase timeout** in agent code (default: 30 seconds)
2. **Check command syntax** for target platform
3. **Verify permissions** - some commands need admin/sudo

### Commands Not Executing

1. **Check agent status** - must be online
2. **View command history** in database:
   ```bash
   sqlite3 server/database.db "SELECT * FROM command_history ORDER BY timestamp DESC LIMIT 10;"
   ```

## Network Issues

### Port Configuration

- **Server Port:** 3000 (HTTP/WebSocket)
- **Agent Connection:** WebSocket to server:3000
- **Firewall Rules:** Allow inbound 3000 on server

### WebSocket Connection Failures

1. **Check proxy/load balancer settings**
2. **Verify WebSocket support** in network infrastructure
3. **Test direct connection** bypassing proxies

## Database Issues

### Corrupt Database

1. **Backup current database:**
   ```bash
   cp server/database.db server/database.db.backup
   ```

2. **Check database integrity:**
   ```bash
   sqlite3 server/database.db "PRAGMA integrity_check;"
   ```

3. **Recreate database** if corrupted:
   ```bash
   rm server/database.db
   npm start  # Will recreate tables
   ```

## Log Locations

### Server Logs
- **Console output** when running `npm start`
- **Admin Panel** → View Update Logs
- **PM2 logs** (if using PM2): `pm2 logs nxtclone`

### Agent Logs

**Linux:**
- **systemd:** `journalctl -u nxtclone-agent`
- **Manual run:** Console output

**Windows:**
- **Event Viewer:** Application → NxtClone Agent
- **Service logs:** Windows Event Log

## Common Error Messages

### "Authentication required"
- **Solution:** Login with admin credentials or clear browser cache

### "Machine not found"
- **Solution:** Check agent connection, restart agent service

### "Command execution failed"
- **Solution:** Verify command syntax, check agent permissions

### "Update failed: repo not found"
- **Solution:** Reinstall agent with latest version from GitHub releases

### "Service not found" or "Permission denied"
- **Solution:** Run tray/control apps as administrator (Windows) or with sudo (Linux)

### "WebSocket connection failed"
- **Solution:** Check server status, firewall settings, network connectivity

## System Tray/Control Applications

### Windows Tray Not Appearing
1. **Check if running:** `tasklist | findstr syswatch-tray`
2. **Run as administrator** if service control needed
3. **Check system tray settings** - may be hidden

### Linux Control App Issues
1. **GUI not available:** App automatically falls back to CLI mode
2. **Permission errors:** Use `sudo` for service operations
3. **Missing dependencies:** Install `python3-tk` for GUI support

### Tray App Features
- **Change Server:** Updates agent configuration
- **Restart Service:** Requires admin/sudo privileges
- **View Logs:** Opens system log viewer
- **About:** Shows version and configuration

## Getting Help

1. **Use tray/control apps** for quick diagnostics and management
2. **Check server console** for error messages
3. **View agent logs** using commands above or tray apps
4. **Check GitHub Issues:** https://github.com/wslabn/nxtclone/releases
5. **Collect diagnostic info:**
   - Server version
   - Agent version (available in tray/control apps)
   - Operating system
   - Error messages
   - Network configuration

## Diagnostic Commands

### Server Health Check
```bash
# Check server process
ps aux | grep node

# Check port binding
netstat -tlnp | grep 3000

# Check database
sqlite3 server/database.db ".tables"
```

### Agent Health Check
```bash
# Linux
systemctl is-active syswatch-agent
systemctl is-enabled syswatch-agent
./syswatch-control  # GUI/CLI interface

# Windows
sc query "SysWatch Agent"
syswatch-tray.exe  # System tray control
```

### Network Connectivity
```bash
# Test server reachability
ping your-server-ip

# Test port connectivity
telnet your-server-ip 3000

# Check DNS resolution
nslookup your-server-hostname
```
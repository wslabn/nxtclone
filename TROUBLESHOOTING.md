# SysWatch Troubleshooting Guide

## Agent Connection Issues

### Check Agent Status

**Linux:**
```bash
# Check service status
systemctl status nxtclone-agent

# View recent logs
journalctl -u nxtclone-agent -n 50

# Follow logs in real-time
journalctl -u nxtclone-agent -f

# Check if agent is running
ps aux | grep nxtclone
```

**Windows:**
```cmd
# Check service status
sc query "NxtClone Agent"

# View service details
sc queryex "NxtClone Agent"

# Check running processes
tasklist | findstr nxtclone
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
   - Linux: `sudo systemctl restart nxtclone-agent`
   - Windows: `sc stop "NxtClone Agent" && sc start "NxtClone Agent"`

## Auto-Update Issues

### Check Agent Version

**Linux:**
```bash
cat /opt/nxtclone/version.txt
```

**Windows:**
```cmd
type "C:\Program Files\NxtClone\NxtClone Agent\version.txt"
```

### Update Troubleshooting

1. **Check GitHub connectivity:**
   ```bash
   curl -I https://api.github.com/repos/wslabn/nxtclone/releases/latest
   ```

2. **Manual update trigger (Linux):**
   ```bash
   sudo touch /tmp/nxtclone-update-now
   ```

3. **View update logs:**
   - **Server:** Admin Panel → View Update Logs
   - **Linux:** `journalctl -u nxtclone-agent -f`
   - **Windows:** Event Viewer → Application → NxtClone Agent

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

### "WebSocket connection failed"
- **Solution:** Check server status, firewall settings, network connectivity

## Getting Help

1. **Check server console** for error messages
2. **View agent logs** using commands above
3. **Check GitHub Issues:** https://github.com/wslabn/nxtclone/issues
4. **Collect diagnostic info:**
   - Server version
   - Agent version
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
systemctl is-active nxtclone-agent
systemctl is-enabled nxtclone-agent

# Windows
sc query "NxtClone Agent"
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
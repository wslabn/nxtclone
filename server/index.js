const WebSocket = require('ws');
const express = require('express');
const http = require('http');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const Database = require('./database');
const Updater = require('./updater');
const AuthManager = require('./auth');
const DiscordNotifier = require('./discord');
const cookieParser = require('cookie-parser');

class RMMServer {
  constructor() {
    this.app = express();
    this.server = http.createServer(this.app);
    this.wss = new WebSocket.Server({ server: this.server });
    this.clients = new Map();
    this.db = new Database();
    this.updater = new Updater();
    this.auth = new AuthManager();
    this.discord = new DiscordNotifier();
    this.groups = new Map(); // Store groups from web clients
    
    // Initialize log storage
    global.serverLogs = global.serverLogs || [];
    this.setupLogging();
    
    this.setupRoutes();
    this.setupWebSocket();
    this.startHeartbeatCheck();
    this.startUpdateCheck();
    this.startTrendAnalysis();
  }
  
  setupLogging() {
    // Capture console.log messages
    const originalLog = console.log;
    console.log = (...args) => {
      const timestamp = new Date().toISOString();
      const message = args.join(' ');
      
      // Store in memory (keep last 200 entries)
      global.serverLogs.push({ timestamp, message, level: 'info' });
      if (global.serverLogs.length > 200) {
        global.serverLogs.shift();
      }
      
      // Call original console.log
      originalLog.apply(console, args);
    };
    
    // Capture console.error messages
    const originalError = console.error;
    console.error = (...args) => {
      const timestamp = new Date().toISOString();
      const message = args.join(' ');
      
      global.serverLogs.push({ timestamp, message, level: 'error' });
      if (global.serverLogs.length > 200) {
        global.serverLogs.shift();
      }
      
      originalError.apply(console, args);
    };
  }

  setupRoutes() {
    this.app.use(cookieParser());
    this.app.use(express.json());
    
    // Public routes
    this.app.get('/login', (req, res) => {
      res.sendFile(path.join(__dirname, '../web/login.html'));
    });
    
    this.app.post('/api/login', (req, res) => {
      const { username, password } = req.body;
      const sessionId = this.auth.authenticate(username, password);
      
      if (sessionId) {
        res.json({ success: true, sessionId });
      } else {
        res.json({ success: false, error: 'Invalid credentials' });
      }
    });
    
    this.app.post('/api/logout', (req, res) => {
      const sessionId = req.cookies?.session;
      if (sessionId) {
        this.auth.sessions.delete(sessionId);
      }
      res.json({ success: true });
    });
    
    this.app.get('/admin', (req, res) => {
      const sessionId = req.cookies?.session;
      const user = sessionId && this.auth.sessions.get(sessionId);
      
      if (!user) {
        res.redirect('/login');
      } else if (user.role !== 'admin') {
        res.status(403).json({ error: 'Admin access required' });
      } else {
        res.sendFile(path.join(__dirname, '../web/admin.html'));
      }
    });
    
    this.app.post('/api/change-password', this.auth.requireAuth.bind(this.auth), (req, res) => {
      const { currentPassword, newPassword } = req.body;
      const success = this.auth.changePassword(req.user.username, currentPassword, newPassword);
      
      if (success) {
        res.json({ success: true });
      } else {
        res.json({ success: false, error: 'Current password is incorrect' });
      }
    });
    
    this.app.post('/api/add-user', this.auth.requireAdmin.bind(this.auth), (req, res) => {
      const { username, password, role } = req.body;
      const success = this.auth.addUser(username, password, role);
      
      if (success) {
        res.json({ success: true });
      } else {
        res.json({ success: false, error: 'Username already exists' });
      }
    });
    
    this.app.get('/api/users', this.auth.requireAdmin.bind(this.auth), (req, res) => {
      res.json(this.auth.getUsers());
    });
    
    this.app.post('/api/delete-user', this.auth.requireAdmin.bind(this.auth), (req, res) => {
      const { username } = req.body;
      const success = this.auth.deleteUser(username);
      
      if (success) {
        res.json({ success: true });
      } else {
        res.json({ success: false, error: 'Cannot delete admin user or user not found' });
      }
    });
    
    this.app.post('/api/discord-webhook', this.auth.requireAdmin.bind(this.auth), (req, res) => {
      const { webhookUrl } = req.body;
      this.discord.setWebhook(webhookUrl);
      res.json({ success: true });
    });
    
    // Default route - redirect to login if not authenticated
    this.app.get('/', (req, res) => {
      const sessionId = req.cookies?.session;
      if (sessionId && this.auth.sessions.has(sessionId)) {
        res.sendFile(path.join(__dirname, '../web/index.html'));
      } else {
        res.redirect('/login');
      }
    });
    
    // Protected routes
    this.app.use('/', (req, res, next) => {
      if (req.path === '/login' || req.path === '/api/login') {
        return next();
      }
      this.auth.requireAuth(req, res, next);
    });
    
    this.app.use(express.static(path.join(__dirname, '../web')));

    // Protected API endpoints
    this.app.get('/api/machines', async (req, res) => {
      const now = Date.now();
      const twentyFourHours = 24 * 60 * 60 * 1000;
      
      // Get machines from memory (current connections)
      const memoryMachines = Array.from(this.clients.values()).map(client => ({
        id: client.id,
        hostname: client.hostname,
        platform: client.platform,
        lastSeen: client.lastSeen,
        status: client.status,
        systemInfo: client.systemInfo || {},
        agentVersion: client.agentVersion || 'Unknown',
        metrics: client.metrics || {}
      }));
      
      // Get machines from database (last 24 hours)
      const dbMachines = await this.db.getMachinesLastSeen(twentyFourHours);
      
      // Merge and deduplicate (memory takes precedence)
      const machineMap = new Map();
      
      // Add database machines first
      dbMachines.forEach(machine => {
        machineMap.set(machine.hostname, {
          id: machine.hostname,
          hostname: machine.hostname,
          platform: machine.platform,
          lastSeen: machine.last_seen,
          status: (now - machine.last_seen) > 30000 ? 'offline' : 'online',
          systemInfo: machine.system_info ? JSON.parse(machine.system_info) : {},
          agentVersion: machine.agent_version || 'Unknown',
          metrics: {}
        });
      });
      
      // Override with memory machines (current connections) but preserve lastSeen for offline
      memoryMachines.forEach(machine => {
        const existing = machineMap.get(machine.hostname);
        if (machine.status === 'offline' && existing && existing.lastSeen > machine.lastSeen) {
          // Keep the more recent lastSeen from database for offline machines
          machine.lastSeen = existing.lastSeen;
        }
        machineMap.set(machine.hostname, machine);
      });
      
      res.json(Array.from(machineMap.values()));
    });
    
    this.app.get('/api/metrics/:machineId', async (req, res) => {
      try {
        const { machineId } = req.params;
        const twentyFourHours = 24 * 60 * 60 * 1000;
        const metrics = await this.db.getMetricsHistory(machineId, twentyFourHours);
        res.json(metrics);
      } catch (error) {
        res.json({ error: error.message });
      }
    });
    
    this.app.get('/api/alerts', async (req, res) => {
      try {
        const alerts = await this.db.getActiveAlerts();
        res.json(alerts);
      } catch (error) {
        res.json({ error: error.message });
      }
    });
    
    this.app.get('/api/alerts/:machineId', async (req, res) => {
      try {
        const { machineId } = req.params;
        const alerts = await this.db.getActiveAlerts(machineId);
        res.json(alerts);
      } catch (error) {
        res.json({ error: error.message });
      }
    });
    
    this.app.get('/api/logs', (req, res) => {
      try {
        // Get recent console logs (stored in memory)
        const logs = global.serverLogs || [];
        res.json({ logs: logs.slice(-100) }); // Last 100 log entries
      } catch (error) {
        res.json({ error: error.message });
      }
    });
    
    this.app.post('/api/uninstall-agent', async (req, res) => {
      try {
        const { machineId } = req.body;
        const client = this.clients.get(machineId);
        
        if (!client || client.ws.readyState !== WebSocket.OPEN) {
          return res.json({ success: false, error: 'Machine not connected' });
        }
        
        client.ws.send(JSON.stringify({ type: 'uninstall_request' }));
        res.json({ success: true });
      } catch (error) {
        res.json({ success: false, error: error.message });
      }
    });

    this.app.post('/api/cleanup-offline', (req, res) => {
      try {
        // Remove offline clients from memory
        let removedCount = 0;
        for (const [id, client] of this.clients.entries()) {
          if (client.status === 'offline') {
            this.clients.delete(id);
            removedCount++;
          }
        }
        
        res.json({ 
          success: true, 
          count: removedCount,
          message: `Removed ${removedCount} offline machines` 
        });
      } catch (error) {
        console.error('Cleanup error:', error);
        res.json({ success: false, error: error.message });
      }
    });

    this.app.post('/api/command', (req, res) => {
      const { machineId, command } = req.body;
      const client = this.clients.get(machineId);
      
      if (!client || client.ws.readyState !== WebSocket.OPEN) {
        return res.json({ success: false, error: 'Machine offline' });
      }

      const commandId = uuidv4();
      client.ws.send(JSON.stringify({
        type: 'command',
        id: commandId,
        command: command
      }));

      res.json({ success: true, commandId });
    });

    this.app.get('/api/update-check', async (req, res) => {
      try {
        const updateInfo = await this.updater.checkForUpdates();
        res.json(updateInfo);
      } catch (error) {
        res.json({ error: error.message });
      }
    });

    this.app.get('/api/command-result/:id', (req, res) => {
      const commandId = req.params.id;
      const result = global.commandResults?.get(commandId);
      
      if (result) {
        res.json({ success: true, result });
        global.commandResults.delete(commandId); // Clean up after retrieval
      } else {
        res.json({ success: false, error: 'Result not found or expired' });
      }
    });

    this.app.get('/api/update-status', (req, res) => {
      const statuses = Array.from(global.updateStatuses?.entries() || []).map(([hostname, status]) => ({
        hostname,
        ...status
      }));
      res.json(statuses);
    });

    this.app.post('/api/update-single-agent', (req, res) => {
      const { machineId } = req.body;
      const client = this.clients.get(machineId);
      
      if (!client || client.ws.readyState !== WebSocket.OPEN) {
        return res.json({ success: false, error: 'Machine not connected' });
      }
      
      const updateCommand = { type: 'update_request' };
      client.ws.send(JSON.stringify(updateCommand));
      
      res.json({ success: true, machineId });
    });

    this.app.post('/api/update-agents', (req, res) => {
      // Clear previous update statuses
      global.updateStatuses = new Map();
      
      // Send update command to all connected agents
      const updateCommand = {
        type: 'update_request'
      };
      
      let updated = 0;
      for (const client of this.clients.values()) {
        if (client.ws.readyState === WebSocket.OPEN) {
          client.ws.send(JSON.stringify(updateCommand));
          updated++;
        }
      }
      
      res.json({ success: true, agentsNotified: updated });
    });
    
    this.app.post('/api/sync-groups', this.auth.requireAuth.bind(this.auth), (req, res) => {
      const { groups } = req.body;
      this.groups = new Map(Object.entries(groups || {}));
      res.json({ success: true });
    });
  }

  setupWebSocket() {
    this.wss.on('connection', (ws) => {
      console.log('New connection');

      ws.on('message', (data) => {
        try {
          const message = JSON.parse(data);
          this.handleMessage(ws, message);
        } catch (error) {
          console.error('Invalid message:', error);
        }
      });

      ws.on('close', () => {
        // Find and remove client
        for (const [id, client] of this.clients.entries()) {
          if (client.ws === ws) {
            const wasOnline = client.status === 'online';
            client.status = 'offline';
            console.log(`Machine ${client.hostname} disconnected`);
            if (wasOnline) {
              const group = this.getMachineGroup(client.hostname);
              this.discord.machineOffline(client.hostname, group);
            }
            break;
          }
        }
      });
    });
  }

  handleMessage(ws, message) {
    switch (message.type) {
      case 'register':
        // Use hostname as static ID
        const clientId = message.hostname;
        const client = {
          id: clientId,
          ws: ws,
          hostname: message.hostname,
          platform: message.platform,
          systemInfo: message.system_info || {},
          agentVersion: message.agentVersion || 'Unknown',
          metrics: {},
          lastSeen: Date.now(),
          status: 'online'
        };
        
        this.clients.set(clientId, client);
        console.log(`Machine registered: ${message.hostname} (${message.platform}) - Agent v${message.agentVersion || 'Unknown'}`);
        
        // Store in database with agent version
        this.db.updateMachine(clientId, message.hostname, message.platform, 'online', message.system_info, message.agentVersion);
        
        // If no version provided, try to get it via command
        if (!message.agentVersion || message.agentVersion === 'Unknown') {
          this.getAgentVersion(client);
        }
        
        ws.send(JSON.stringify({
          type: 'registered',
          id: clientId
        }));
        break;

      case 'heartbeat':
        // Update last seen and metrics
        for (const client of this.clients.values()) {
          if (client.ws === ws) {
            client.lastSeen = Date.now();
            client.status = 'online';
            const metrics = message.metrics || {};
            
            // Check for high resource usage alerts
            const group = this.getMachineGroup(client.hostname);
            if (metrics.cpu_percent > 89) {
              this.discord.highResourceUsage(client.hostname, 'CPU', metrics.cpu_percent.toFixed(1), group);
            }
            if (metrics.memory_percent > 89) {
              this.discord.highResourceUsage(client.hostname, 'Memory', metrics.memory_percent.toFixed(1), group);
            }
            if (metrics.disk_percent > 89) {
              this.discord.highResourceUsage(client.hostname, 'Disk', metrics.disk_percent.toFixed(1), group);
            }
            
            client.metrics = metrics;
            
            // Store metrics in database for historical tracking
            this.db.storeMetrics(client.id, metrics);
            
            // Check for immediate anomalies
            this.checkMetricAnomalies(client.id, client.hostname, metrics);
            break;
          }
        }
        break;

      case 'command_result':
        console.log(`Command result from ${message.hostname}:`, message.result);
        
        // Check if this is a version command response
        const machineClient = Array.from(this.clients.values()).find(c => c.hostname === message.hostname);
        if (machineClient && machineClient.versionCommandId === message.id) {
          const version = message.result.stdout?.trim() || 'Unknown';
          if (version !== 'Unknown' && version !== '') {
            machineClient.agentVersion = version;
            this.db.updateMachine(machineClient.id, machineClient.hostname, machineClient.platform, machineClient.status, machineClient.systemInfo, version);
            console.log(`Updated agent version for ${message.hostname}: ${version}`);
          }
          delete machineClient.versionCommandId;
        }
        
        // Store result for web client retrieval
        global.commandResults = global.commandResults || new Map();
        global.commandResults.set(message.id, {
          hostname: message.hostname,
          result: message.result,
          timestamp: Date.now()
        });
        break;
        
      case 'update_status':
        console.log(`Update status from ${message.hostname}: ${message.status}`);
        // Store update status
        global.updateStatuses = global.updateStatuses || new Map();
        global.updateStatuses.set(message.hostname, {
          status: message.status,
          version: message.version,
          error: message.error,
          timestamp: Date.now()
        });
        break;
        
      case 'agent_log':
        console.log(`[${message.hostname}] ${message.message}`);
        // Store agent log in server logs
        global.serverLogs.push({
          timestamp: new Date().toISOString(),
          message: `[${message.hostname}] ${message.message}`,
          level: 'info'
        });
        if (global.serverLogs.length > 200) {
          global.serverLogs.shift();
        }
        
        // Send Discord alert for uninstall
        if (message.message.includes('Agent uninstalled successfully')) {
          this.discord.agentUninstalled(message.hostname);
        }
        break;
    }
  }

  startHeartbeatCheck() {
    setInterval(() => {
      const now = Date.now();
      const timeout = 30000; // 30 seconds

      for (const client of this.clients.values()) {
        if (now - client.lastSeen > timeout && client.status === 'online') {
          client.status = 'offline';
          // Update database with current offline time
          this.db.updateMachine(client.id, client.hostname, client.platform, 'offline', client.systemInfo);
          console.log(`ALERT: Machine ${client.hostname} went offline`);
          const group = this.getMachineGroup(client.hostname);
          this.discord.machineOffline(client.hostname, group);
        }
      }
    }, 10000); // Check every 10 seconds
  }

  startUpdateCheck() {
    // Check for updates every 30 minutes and auto-notify agents
    this.updater.startAutoUpdateCheck(30);
    
    // Listen for server updates to trigger agent updates
    this.updater.onUpdateAvailable = () => {
      this.notifyAllAgentsToUpdate();
    };
  }
  
  notifyAllAgentsToUpdate() {
    console.log('Notifying all agents to update...');
    const updateCommand = { type: 'update_request' };
    
    for (const client of this.clients.values()) {
      if (client.ws.readyState === WebSocket.OPEN) {
        client.ws.send(JSON.stringify(updateCommand));
      }
    }
  }

  getMachineGroup(hostname) {
    for (const [groupName, machines] of this.groups.entries()) {
      if (machines.includes(hostname)) {
        return groupName;
      }
    }
    return 'Unknown';
  }
  
  getAgentVersion(client) {
    if (client.ws.readyState !== WebSocket.OPEN) return;
    
    const isWindows = client.platform.includes('Windows');
    const versionCommand = isWindows ? 
      'type "C:\\Program Files\\SysWatch\\version.txt" 2>nul || type "C:\\Program Files (x86)\\SysWatch\\version.txt" 2>nul || echo Unknown' :
      'cat /opt/syswatch/version.txt 2>/dev/null || echo Unknown';
    
    const commandId = uuidv4();
    client.ws.send(JSON.stringify({
      type: 'command',
      id: commandId,
      command: versionCommand
    }));
    
    // Store command ID to identify version response
    client.versionCommandId = commandId;
  }
  
  startTrendAnalysis() {
    // Run trend analysis every 30 minutes
    setInterval(async () => {
      console.log('Running trend analysis...');
      
      for (const client of this.clients.values()) {
        if (client.status === 'online') {
          await this.analyzeTrends(client.id, client.hostname);
        }
      }
    }, 30 * 60 * 1000); // 30 minutes
  }
  
  async checkMetricAnomalies(machineId, hostname, currentMetrics) {
    try {
      // Get baseline for comparison
      const cpuBaseline = await this.db.calculateBaseline(machineId, 'cpu_percent');
      const memoryBaseline = await this.db.calculateBaseline(machineId, 'memory_percent');
      const diskBaseline = await this.db.calculateBaseline(machineId, 'disk_percent');
      
      // Check for significant deviations (3x baseline average)
      if (cpuBaseline.avg && currentMetrics.cpu_percent > cpuBaseline.avg * 3) {
        this.db.storeAlert(machineId, 'anomaly', 'warning', 
          `CPU usage (${currentMetrics.cpu_percent.toFixed(1)}%) is 3x higher than baseline (${cpuBaseline.avg.toFixed(1)}%)`,
          { current: currentMetrics.cpu_percent, baseline: cpuBaseline.avg }
        );
        
        const group = this.getMachineGroup(hostname);
        this.discord.sendProactiveAlert(`🚨 **CPU Anomaly**: ${hostname} CPU at ${currentMetrics.cpu_percent.toFixed(1)}% (baseline: ${cpuBaseline.avg.toFixed(1)}%) [${group}]`);
      }
      
      if (memoryBaseline.avg && currentMetrics.memory_percent > memoryBaseline.avg * 2.5) {
        this.db.storeAlert(machineId, 'anomaly', 'warning',
          `Memory usage (${currentMetrics.memory_percent.toFixed(1)}%) is significantly higher than baseline (${memoryBaseline.avg.toFixed(1)}%)`,
          { current: currentMetrics.memory_percent, baseline: memoryBaseline.avg }
        );
        
        const group = this.getMachineGroup(hostname);
        this.discord.sendProactiveAlert(`🧠 **Memory Anomaly**: ${hostname} Memory at ${currentMetrics.memory_percent.toFixed(1)}% (baseline: ${memoryBaseline.avg.toFixed(1)}%) [${group}]`);
      }
      
    } catch (error) {
      console.error('Error checking metric anomalies:', error);
    }
  }
  
  async analyzeTrends(machineId, hostname) {
    try {
      // Analyze disk space trend for predictive alerts
      const diskTrend = await this.db.getTrend(machineId, 'disk_percent', 48);
      
      if (diskTrend.slope > 0.5 && diskTrend.dataPoints > 10) {
        // Disk usage increasing significantly
        const daysUntilFull = diskTrend.prediction > 95 ? 
          Math.ceil((95 - diskTrend.prediction) / (diskTrend.slope * 24 * 6)) : null;
        
        if (daysUntilFull && daysUntilFull < 7) {
          this.db.storeAlert(machineId, 'predictive', 'critical',
            `Disk space trending toward full - estimated ${daysUntilFull} days remaining`,
            { trend: diskTrend, daysUntilFull }
          );
          
          const group = this.getMachineGroup(hostname);
          this.discord.sendProactiveAlert(`💾 **Disk Space Warning**: ${hostname} disk will be full in ~${daysUntilFull} days at current rate [${group}]`);
        }
      }
      
      // Analyze CPU performance degradation
      const cpuTrend = await this.db.getTrend(machineId, 'cpu_percent', 24);
      
      if (cpuTrend.slope > 1.0 && cpuTrend.dataPoints > 20) {
        this.db.storeAlert(machineId, 'trend', 'warning',
          `CPU usage trending upward - ${(cpuTrend.slope * 24).toFixed(1)}% increase per day`,
          { trend: cpuTrend }
        );
        
        const group = this.getMachineGroup(hostname);
        this.discord.sendProactiveAlert(`📈 **Performance Trend**: ${hostname} CPU usage increasing ${(cpuTrend.slope * 24).toFixed(1)}%/day [${group}]`);
      }
      
    } catch (error) {
      console.error('Error analyzing trends:', error);
    }
  }

  start(port = 3000) {
    this.server.listen(port, () => {
      console.log(`RMM Server running on port ${port}`);
    });
  }
}

const server = new RMMServer();
server.start();
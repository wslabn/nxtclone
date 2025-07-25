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
    
    this.setupRoutes();
    this.setupWebSocket();
    this.startHeartbeatCheck();
    this.startUpdateCheck();
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
    
    this.app.get('/admin', this.auth.requireAdmin.bind(this.auth), (req, res) => {
      res.sendFile(path.join(__dirname, '../web/admin.html'));
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
    
    // Protected routes
    this.app.use('/', (req, res, next) => {
      if (req.path === '/login' || req.path === '/api/login') {
        return next();
      }
      this.auth.requireAuth(req, res, next);
    });
    
    this.app.use(express.static(path.join(__dirname, '../web')));

    // Protected API endpoints
    this.app.get('/api/machines', (req, res) => {
      const machines = Array.from(this.clients.values()).map(client => ({
        id: client.id,
        hostname: client.hostname,
        platform: client.platform,
        lastSeen: client.lastSeen,
        status: client.status,
        systemInfo: client.systemInfo || {},
        agentVersion: client.agentVersion || 'Unknown',
        metrics: client.metrics || {}
      }));
      res.json(machines);
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
          agentVersion: message.agent_version || 'Unknown',
          metrics: {},
          lastSeen: Date.now(),
          status: 'online'
        };
        
        this.clients.set(clientId, client);
        console.log(`Machine registered: ${message.hostname} (${message.platform}) - Agent v${message.agent_version || 'Unknown'}`);
        
        // Store in database
        this.db.updateMachine(clientId, message.hostname, message.platform, 'online', message.system_info);
        
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
            break;
          }
        }
        break;

      case 'command_result':
        console.log(`Command result from ${message.hostname}:`, message.result);
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
    }
  }

  startHeartbeatCheck() {
    setInterval(() => {
      const now = Date.now();
      const timeout = 30000; // 30 seconds

      for (const client of this.clients.values()) {
        if (now - client.lastSeen > timeout && client.status === 'online') {
          client.status = 'offline';
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

  start(port = 3000) {
    this.server.listen(port, () => {
      console.log(`RMM Server running on port ${port}`);
    });
  }
}

const server = new RMMServer();
server.start();
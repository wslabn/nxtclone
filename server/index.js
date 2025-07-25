const WebSocket = require('ws');
const express = require('express');
const http = require('http');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const Database = require('./database');
const Updater = require('./updater');

class RMMServer {
  constructor() {
    this.app = express();
    this.server = http.createServer(this.app);
    this.wss = new WebSocket.Server({ server: this.server });
    this.clients = new Map();
    this.db = new Database();
    this.updater = new Updater();
    
    this.setupRoutes();
    this.setupWebSocket();
    this.startHeartbeatCheck();
    this.startUpdateCheck();
  }

  setupRoutes() {
    this.app.use(express.static(path.join(__dirname, '../web')));
    this.app.use(express.json());

    // API endpoints
    this.app.get('/api/machines', (req, res) => {
      const machines = Array.from(this.clients.values()).map(client => ({
        id: client.id,
        hostname: client.hostname,
        platform: client.platform,
        lastSeen: client.lastSeen,
        status: client.status,
        systemInfo: client.systemInfo || {},
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

    this.app.post('/api/update-agents', (req, res) => {
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
            client.status = 'offline';
            console.log(`Machine ${client.hostname} disconnected`);
            break;
          }
        }
      });
    });
  }

  handleMessage(ws, message) {
    switch (message.type) {
      case 'register':
        const clientId = uuidv4();
        const client = {
          id: clientId,
          ws: ws,
          hostname: message.hostname,
          platform: message.platform,
          systemInfo: message.system_info || {},
          metrics: {},
          lastSeen: Date.now(),
          status: 'online'
        };
        
        this.clients.set(clientId, client);
        console.log(`Machine registered: ${message.hostname} (${message.platform})`);
        
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
            client.metrics = message.metrics || {};
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
          // Here you could send alerts via email, Slack, etc.
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

  start(port = 3000) {
    this.server.listen(port, () => {
      console.log(`RMM Server running on port ${port}`);
    });
  }
}

const server = new RMMServer();
server.start();
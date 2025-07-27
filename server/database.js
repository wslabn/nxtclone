const sqlite3 = require('sqlite3').verbose();
const path = require('path');

class Database {
  constructor() {
    this.db = new sqlite3.Database(path.join(__dirname, 'rmm.db'));
    this.init();
  }

  init() {
    this.db.serialize(() => {
      this.db.run(`
        CREATE TABLE IF NOT EXISTS machines (
          id TEXT PRIMARY KEY,
          hostname TEXT,
          platform TEXT,
          system_info TEXT,
          last_seen INTEGER,
          status TEXT,
          agent_version TEXT DEFAULT 'Unknown',
          created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
      `);

      this.db.run(`
        CREATE TABLE IF NOT EXISTS commands (
          id TEXT PRIMARY KEY,
          machine_id TEXT,
          command TEXT,
          result TEXT,
          executed_at INTEGER,
          created_at INTEGER DEFAULT (strftime('%s', 'now')),
          FOREIGN KEY (machine_id) REFERENCES machines (id)
        )
      `);
      
      this.db.run(`
        CREATE TABLE IF NOT EXISTS metrics (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          machine_id TEXT,
          cpu_percent REAL,
          memory_percent REAL,
          disk_percent REAL,
          process_count INTEGER,
          timestamp INTEGER,
          FOREIGN KEY (machine_id) REFERENCES machines (id)
        )
      `);
      
      // Create index for faster queries
      this.db.run(`CREATE INDEX IF NOT EXISTS idx_metrics_machine_time ON metrics (machine_id, timestamp)`);
      
      this.db.run(`
        CREATE TABLE IF NOT EXISTS alerts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          machine_id TEXT,
          alert_type TEXT,
          severity TEXT,
          message TEXT,
          data TEXT,
          timestamp INTEGER,
          acknowledged INTEGER DEFAULT 0,
          FOREIGN KEY (machine_id) REFERENCES machines (id)
        )
      `);
      
      this.db.run(`CREATE INDEX IF NOT EXISTS idx_alerts_machine_time ON alerts (machine_id, timestamp)`);
      
      // Agent groups table
      this.db.run(`
        CREATE TABLE IF NOT EXISTS agent_groups (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT UNIQUE NOT NULL,
          description TEXT,
          color TEXT DEFAULT '#007bff',
          created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
      `);
      
      // Agent group memberships
      this.db.run(`
        CREATE TABLE IF NOT EXISTS agent_group_members (
          group_id INTEGER,
          machine_id TEXT,
          added_at INTEGER DEFAULT (strftime('%s', 'now')),
          PRIMARY KEY (group_id, machine_id),
          FOREIGN KEY (group_id) REFERENCES agent_groups (id) ON DELETE CASCADE,
          FOREIGN KEY (machine_id) REFERENCES machines (id) ON DELETE CASCADE
        )
      `);
      
      // Agent configurations
      this.db.run(`
        CREATE TABLE IF NOT EXISTS agent_configs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          machine_id TEXT,
          config_key TEXT,
          config_value TEXT,
          applied_at INTEGER,
          created_at INTEGER DEFAULT (strftime('%s', 'now')),
          FOREIGN KEY (machine_id) REFERENCES machines (id) ON DELETE CASCADE
        )
      `);
      
      this.db.run(`CREATE INDEX IF NOT EXISTS idx_agent_configs_machine ON agent_configs (machine_id)`);
      
      // Add agent_version column if it doesn't exist (migration)
      this.db.run(`ALTER TABLE machines ADD COLUMN agent_version TEXT DEFAULT 'Unknown'`, (err) => {
        if (err && !err.message.includes('duplicate column')) {
          console.error('Migration error:', err.message);
        }
      });
      
      // Clean up old metrics (keep only 7 days)
      this.db.run(`DELETE FROM metrics WHERE timestamp < ?`, [Date.now() - (7 * 24 * 60 * 60 * 1000)]);
      this.db.run(`DELETE FROM alerts WHERE timestamp < ?`, [Date.now() - (7 * 24 * 60 * 60 * 1000)]);
    });
  }

  updateMachine(id, hostname, platform, status, systemInfo = null, agentVersion = 'Unknown') {
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO machines (id, hostname, platform, system_info, last_seen, status, agent_version)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);
    stmt.run(id, hostname, platform, systemInfo ? JSON.stringify(systemInfo) : null, Date.now(), status, agentVersion);
    stmt.finalize();
  }

  logCommand(id, machineId, command, result) {
    const stmt = this.db.prepare(`
      INSERT INTO commands (id, machine_id, command, result, executed_at)
      VALUES (?, ?, ?, ?, ?)
    `);
    stmt.run(id, machineId, command, result, Date.now());
    stmt.finalize();
  }
  
  getMachinesLastSeen(timeWindow) {
    return new Promise((resolve, reject) => {
      const cutoff = Date.now() - timeWindow;
      this.db.all(`
        SELECT id, hostname, platform, system_info, last_seen, status, 
               CASE WHEN system_info IS NOT NULL 
                    THEN json_extract(system_info, '$.agent_version') 
                    ELSE NULL END as agent_version
        FROM machines 
        WHERE last_seen > ?
        ORDER BY last_seen DESC
      `, [cutoff], (err, rows) => {
        if (err) {
          reject(err);
        } else {
          resolve(rows);
        }
      });
    });
  }
  
  storeMetrics(machineId, metrics) {
    const stmt = this.db.prepare(`
      INSERT INTO metrics (machine_id, cpu_percent, memory_percent, disk_percent, process_count, timestamp)
      VALUES (?, ?, ?, ?, ?, ?)
    `);
    stmt.run(
      machineId, 
      metrics.cpu_percent || 0, 
      metrics.memory_percent || 0, 
      metrics.disk_percent || 0, 
      metrics.process_count || 0, 
      Date.now()
    );
    stmt.finalize();
  }
  
  getMetricsHistory(machineId, timeWindow) {
    return new Promise((resolve, reject) => {
      const cutoff = Date.now() - timeWindow;
      this.db.all(`
        SELECT cpu_percent, memory_percent, disk_percent, process_count, timestamp
        FROM metrics 
        WHERE machine_id = ? AND timestamp > ?
        ORDER BY timestamp ASC
      `, [machineId, cutoff], (err, rows) => {
        if (err) {
          reject(err);
        } else {
          resolve(rows);
        }
      });
    });
  }
  
  calculateBaseline(machineId, metric, days = 7) {
    return new Promise((resolve, reject) => {
      const cutoff = Date.now() - (days * 24 * 60 * 60 * 1000);
      this.db.all(`
        SELECT AVG(${metric}) as avg, 
               MIN(${metric}) as min, 
               MAX(${metric}) as max,
               COUNT(*) as count
        FROM metrics 
        WHERE machine_id = ? AND timestamp > ?
      `, [machineId, cutoff], (err, rows) => {
        if (err) {
          reject(err);
        } else {
          resolve(rows[0]);
        }
      });
    });
  }
  
  getTrend(machineId, metric, hours = 24) {
    return new Promise((resolve, reject) => {
      const cutoff = Date.now() - (hours * 60 * 60 * 1000);
      this.db.all(`
        SELECT ${metric} as value, timestamp
        FROM metrics 
        WHERE machine_id = ? AND timestamp > ?
        ORDER BY timestamp ASC
      `, [machineId, cutoff], (err, rows) => {
        if (err) {
          reject(err);
        } else {
          // Calculate linear regression for trend
          if (rows.length < 2) {
            resolve({ slope: 0, correlation: 0, prediction: null });
            return;
          }
          
          const n = rows.length;
          const sumX = rows.reduce((sum, row, i) => sum + i, 0);
          const sumY = rows.reduce((sum, row) => sum + row.value, 0);
          const sumXY = rows.reduce((sum, row, i) => sum + (i * row.value), 0);
          const sumXX = rows.reduce((sum, row, i) => sum + (i * i), 0);
          
          const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
          const intercept = (sumY - slope * sumX) / n;
          
          // Predict value 24 hours from now
          const futureIndex = n + (24 * 6); // Assuming 10-minute intervals
          const prediction = slope * futureIndex + intercept;
          
          resolve({ slope, intercept, prediction, dataPoints: n });
        }
      });
    });
  }
  
  storeAlert(machineId, alertType, severity, message, data = null) {
    const stmt = this.db.prepare(`
      INSERT INTO alerts (machine_id, alert_type, severity, message, data, timestamp)
      VALUES (?, ?, ?, ?, ?, ?)
    `);
    stmt.run(machineId, alertType, severity, message, data ? JSON.stringify(data) : null, Date.now());
    stmt.finalize();
  }
  
  getActiveAlerts(machineId = null) {
    return new Promise((resolve, reject) => {
      const query = machineId ? 
        'SELECT * FROM alerts WHERE machine_id = ? AND acknowledged = 0 ORDER BY timestamp DESC' :
        'SELECT * FROM alerts WHERE acknowledged = 0 ORDER BY timestamp DESC';
      const params = machineId ? [machineId] : [];
      
      this.db.all(query, params, (err, rows) => {
        if (err) {
          reject(err);
        } else {
          resolve(rows);
        }
      });
    });
  }
  
  // Agent Groups
  createGroup(name, description, color = '#007bff') {
    return new Promise((resolve, reject) => {
      const stmt = this.db.prepare('INSERT INTO agent_groups (name, description, color) VALUES (?, ?, ?)');
      stmt.run(name, description, color, function(err) {
        if (err) reject(err);
        else resolve(this.lastID);
      });
      stmt.finalize();
    });
  }
  
  getGroups() {
    return new Promise((resolve, reject) => {
      this.db.all(`
        SELECT g.*, COUNT(m.machine_id) as member_count
        FROM agent_groups g
        LEFT JOIN agent_group_members m ON g.id = m.group_id
        GROUP BY g.id
        ORDER BY g.name
      `, (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });
  }
  
  addToGroup(groupId, machineId) {
    const stmt = this.db.prepare('INSERT OR IGNORE INTO agent_group_members (group_id, machine_id) VALUES (?, ?)');
    stmt.run(groupId, machineId);
    stmt.finalize();
  }
  
  removeFromGroup(groupId, machineId) {
    const stmt = this.db.prepare('DELETE FROM agent_group_members WHERE group_id = ? AND machine_id = ?');
    stmt.run(groupId, machineId);
    stmt.finalize();
  }
  
  getGroupMembers(groupId) {
    return new Promise((resolve, reject) => {
      this.db.all(`
        SELECT m.*, g.name as group_name
        FROM machines m
        JOIN agent_group_members gm ON m.id = gm.machine_id
        JOIN agent_groups g ON gm.group_id = g.id
        WHERE g.id = ?
      `, [groupId], (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });
  }
  
  // Agent Configuration
  setAgentConfig(machineId, configKey, configValue) {
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO agent_configs (machine_id, config_key, config_value)
      VALUES (?, ?, ?)
    `);
    stmt.run(machineId, configKey, configValue);
    stmt.finalize();
  }
  
  getAgentConfig(machineId) {
    return new Promise((resolve, reject) => {
      this.db.all(
        'SELECT config_key, config_value, applied_at FROM agent_configs WHERE machine_id = ?',
        [machineId],
        (err, rows) => {
          if (err) reject(err);
          else {
            const config = {};
            rows.forEach(row => {
              config[row.config_key] = {
                value: row.config_value,
                applied_at: row.applied_at
              };
            });
            resolve(config);
          }
        }
      );
    });
  }
  
  markConfigApplied(machineId, configKey) {
    const stmt = this.db.prepare(
      'UPDATE agent_configs SET applied_at = ? WHERE machine_id = ? AND config_key = ?'
    );
    stmt.run(Date.now(), machineId, configKey);
    stmt.finalize();
  }
}

module.exports = Database;
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
    });
  }

  updateMachine(id, hostname, platform, status, systemInfo = null) {
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO machines (id, hostname, platform, system_info, last_seen, status)
      VALUES (?, ?, ?, ?, ?, ?)
    `);
    stmt.run(id, hostname, platform, systemInfo ? JSON.stringify(systemInfo) : null, Date.now(), status);
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
}

module.exports = Database;
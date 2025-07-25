const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

class AuthManager {
  constructor() {
    this.usersFile = path.join(__dirname, 'users.json');
    this.sessions = new Map();
    this.loadUsers();
  }
  
  loadUsers() {
    try {
      const data = JSON.parse(fs.readFileSync(this.usersFile, 'utf8'));
      this.users = new Map(Object.entries(data));
    } catch {
      // Default admin user if no file exists
      this.users = new Map([
        ['admin', {
          username: 'admin',
          passwordHash: this.hashPassword('admin123'),
          role: 'admin'
        }]
      ]);
      this.saveUsers();
    }
  }
  
  saveUsers() {
    const data = Object.fromEntries(this.users);
    fs.writeFileSync(this.usersFile, JSON.stringify(data, null, 2));
  }

  hashPassword(password) {
    return crypto.createHash('sha256').update(password + 'nxtclone-salt').digest('hex');
  }

  authenticate(username, password) {
    const user = this.users.get(username);
    if (!user) return null;
    
    const passwordHash = this.hashPassword(password);
    if (passwordHash === user.passwordHash) {
      const sessionId = crypto.randomUUID();
      this.sessions.set(sessionId, {
        username: user.username,
        role: user.role,
        created: Date.now()
      });
      return sessionId;
    }
    return null;
  }

  validateSession(sessionId) {
    const session = this.sessions.get(sessionId);
    if (!session) return null;
    
    // Session expires after 24 hours
    if (Date.now() - session.created > 24 * 60 * 60 * 1000) {
      this.sessions.delete(sessionId);
      return null;
    }
    
    return session;
  }
  
  changePassword(username, currentPassword, newPassword) {
    const user = this.users.get(username);
    if (!user) return false;
    
    const currentHash = this.hashPassword(currentPassword);
    if (currentHash !== user.passwordHash) return false;
    
    user.passwordHash = this.hashPassword(newPassword);
    this.saveUsers();
    return true;
  }
  
  addUser(username, password, role = 'user') {
    if (this.users.has(username)) return false;
    
    this.users.set(username, {
      username,
      passwordHash: this.hashPassword(password),
      role
    });
    this.saveUsers();
    return true;
  }
  
  deleteUser(username) {
    if (username === 'admin') return false; // Protect admin user
    const result = this.users.delete(username);
    if (result) this.saveUsers();
    return result;
  }
  
  getUsers() {
    return Array.from(this.users.values()).map(user => ({
      username: user.username,
      role: user.role
    }));
  }

  requireAuth(req, res, next) {
    const sessionId = req.cookies?.session || req.headers['x-session-id'];
    const session = this.validateSession(sessionId);
    
    if (!session) {
      return res.status(401).json({ error: 'Authentication required' });
    }
    
    req.user = session;
    next();
  }
  
  requireAdmin(req, res, next) {
    this.requireAuth(req, res, (err) => {
      if (err) return next(err);
      if (req.user.role !== 'admin') {
        return res.status(403).json({ error: 'Admin access required' });
      }
      next();
    });
  }
}

module.exports = AuthManager;
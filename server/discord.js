const fs = require('fs');
const path = require('path');

class DiscordNotifier {
  constructor() {
    this.configFile = path.join(__dirname, 'discord-config.json');
    this.loadConfig();
  }

  loadConfig() {
    try {
      const config = JSON.parse(fs.readFileSync(this.configFile, 'utf8'));
      this.webhookUrl = config.webhookUrl;
    } catch {
      this.webhookUrl = null;
    }
  }

  setWebhook(url) {
    this.webhookUrl = url;
    fs.writeFileSync(this.configFile, JSON.stringify({ webhookUrl: url }));
  }

  async sendAlert(title, message, color = 0xff0000) {
    console.log(`Discord alert: ${title} - ${message}`);
    console.log(`Webhook URL configured: ${!!this.webhookUrl}`);
    
    if (!this.webhookUrl) {
      console.log('No Discord webhook URL configured');
      return false;
    }

    const embed = {
      title: title,
      description: message,
      color: color,
      timestamp: new Date().toISOString(),
      footer: {
        text: "SysWatch RMM"
      }
    };

    try {
      console.log('Sending Discord notification...');
      const response = await fetch(this.webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ embeds: [embed] })
      });

      console.log(`Discord response: ${response.status}`);
      return response.ok;
    } catch (error) {
      console.error('Discord notification failed:', error);
      return false;
    }
  }

  async machineOffline(hostname, group = 'Unknown') {
    return this.sendAlert(
      '🔴 Machine Offline',
      `**${hostname}** (${group}) has gone offline`,
      0xff0000
    );
  }

  async machineOnline(hostname, group = 'Unknown') {
    return this.sendAlert(
      '🟢 Machine Online',
      `**${hostname}** (${group}) is back online`,
      0x00ff00
    );
  }

  async highResourceUsage(hostname, resource, usage, group = 'Unknown') {
    return this.sendAlert(
      '⚠️ High Resource Usage',
      `**${hostname}** (${group}) - ${resource}: ${usage}%`,
      0xffa500
    );
  }
  
  async agentUninstalled(hostname, group = 'Unknown') {
    return this.sendAlert(
      '🗑️ Agent Uninstalled',
      `**${hostname}** (${group}) - SysWatch agent has been removed`,
      0xff5722
    );
  }
  
  async sendProactiveAlert(message) {
    if (!this.webhookUrl) return false;
    
    try {
      const response = await fetch(this.webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          content: message,
          username: 'SysWatch Alerts'
        })
      });
      
      return response.ok;
    } catch (error) {
      console.error('Discord proactive alert failed:', error);
      return false;
    }
  }
}

module.exports = DiscordNotifier;
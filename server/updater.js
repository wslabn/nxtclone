const https = require('https');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class Updater {
  constructor(repoOwner = 'your-username', repoName = 'nxtclone') {
    this.repoOwner = repoOwner;
    this.repoName = repoName;
    this.currentVersion = this.getCurrentVersion();
  }

  getCurrentVersion() {
    try {
      const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, '../package.json'), 'utf8'));
      return packageJson.version;
    } catch (error) {
      return '1.0.0';
    }
  }

  async checkForUpdates() {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: 'api.github.com',
        path: `/repos/${this.repoOwner}/${this.repoName}/releases/latest`,
        headers: { 'User-Agent': 'nxtclone-updater' }
      };

      https.get(options, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try {
            if (!data) {
              reject(new Error('No data received from GitHub API'));
              return;
            }
            
            const release = JSON.parse(data);
            if (!release.tag_name) {
              // No releases found, return current version as latest
              resolve({
                hasUpdate: false,
                currentVersion: this.currentVersion,
                latestVersion: this.currentVersion,
                downloadUrl: null,
                releaseNotes: 'No releases found'
              });
              return;
            }
            
            const latestVersion = release.tag_name.replace('v', '');
            
            const updateInfo = {
              hasUpdate: this.compareVersions(latestVersion, this.currentVersion) > 0,
              currentVersion: this.currentVersion,
              latestVersion: latestVersion,
              downloadUrl: release.zipball_url,
              releaseNotes: release.body
            };
            
            // Auto-update if new version available
            if (updateInfo.hasUpdate) {
              console.log(`Auto-updating server: ${updateInfo.currentVersion} -> ${updateInfo.latestVersion}`);
              this.downloadAndUpdate(updateInfo.downloadUrl);
            }
            
            resolve(updateInfo);
          } catch (error) {
            reject(error);
          }
        });
      }).on('error', reject);
    });
  }

  compareVersions(a, b) {
    const aParts = a.split('.').map(Number);
    const bParts = b.split('.').map(Number);
    
    for (let i = 0; i < Math.max(aParts.length, bParts.length); i++) {
      const aPart = aParts[i] || 0;
      const bPart = bParts[i] || 0;
      
      if (aPart > bPart) return 1;
      if (aPart < bPart) return -1;
    }
    return 0;
  }

  async downloadAndUpdate(downloadUrl) {
    console.log('Downloading update...');
    
    // In a real implementation, you would:
    // 1. Download the release zip
    // 2. Extract to temp directory
    // 3. Stop current process
    // 4. Replace files
    // 5. Restart process
    
    // For now, just log the process
    console.log('Update downloaded. Restart required.');
    return true;
  }

  startAutoUpdateCheck(intervalMinutes = 30) {
    // Check immediately on startup
    setTimeout(() => this.checkForUpdates().catch(console.error), 5000);
    
    // Then check every 30 minutes
    setInterval(async () => {
      try {
        await this.checkForUpdates();
      } catch (error) {
        console.error('Auto-update check failed:', error.message);
      }
    }, intervalMinutes * 60 * 1000);
  }
}

module.exports = Updater;
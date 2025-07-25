# Deployment & Auto-Update Setup

## GitHub Repository Setup

1. **Create GitHub Repository:**
   - Go to https://github.com/new
   - Name: `nxtclone`
   - Make it Public
   - Don't initialize with README
   - Click "Create repository"

2. **Initialize Git:**
   ```bash
   cd \projects\nxtclone
   git init
   git add .
   git commit -m "Initial RMM system with auto-update"
   git remote add origin https://github.com/YOUR-USERNAME/nxtclone.git
   git branch -M main
   git push -u origin main
   ```

3. **Update Repository Info:**
   Replace YOUR-USERNAME with your actual GitHub username in:
   - `server/updater.js` line 6
   - `agents/agent_updater.py` line 8

## Creating Your First Release

1. **Tag and Push:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Create GitHub Release:**
   - Go to your repo → Releases → "Create a new release"
   - Tag: v1.0.0
   - Title: "Initial Release"
   - Description: "First release with auto-update functionality"
   - Click "Publish release"

## Auto-Update Features

### Server Updates
- Checks GitHub releases every hour
- API endpoint: `GET /api/update-check`
- Manual update check via dashboard

### Agent Updates
- Responds to server update requests
- Downloads and installs updates automatically
- Restarts after successful update
- Manual trigger via dashboard "Update All Agents" button

### Update Process
1. Server checks for new releases
2. Dashboard shows update availability
3. Click "Update All Agents" to notify agents
4. Agents download, install, and restart automatically

## Version Management

- Server version: `package.json` → `version`
- Agent version: `agents/version.txt`
- Update both when creating new releases

## Security Notes

For production deployment:
- Use HTTPS for GitHub API calls
- Implement signature verification for downloads
- Add authentication for update endpoints
- Use environment variables for repository info
#!/bin/bash

# NxtClone Linux Agent Installer
# Usage: sudo ./install-linux.sh [server_url]
# Example: sudo ./install-linux.sh ws://192.168.1.100:3000

set -e

# Get server URL from parameter or use default
SERVER_URL="${1:-ws://localhost:3000}"

echo "Installing NxtClone Agent..."
echo "Server URL: $SERVER_URL"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    echo "Usage: sudo ./install-linux.sh [server_url]"
    exit 1
fi

# Create installation directory
mkdir -p /opt/nxtclone

# Copy agent executable
cp nxtclone-agent-linux /opt/nxtclone/nxtclone-agent
chmod +x /opt/nxtclone/nxtclone-agent

# Create systemd service file
cat > /etc/systemd/system/nxtclone-agent.service << EOF
[Unit]
Description=NxtClone Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nxtclone
ExecStart=/opt/nxtclone/nxtclone-agent $SERVER_URL
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable nxtclone-agent
systemctl start nxtclone-agent

echo "NxtClone Agent installed successfully!"
echo "Service status:"
systemctl status nxtclone-agent --no-pager -l

echo ""
echo "To check logs: sudo journalctl -u nxtclone-agent -f"
echo "To restart: sudo systemctl restart nxtclone-agent"
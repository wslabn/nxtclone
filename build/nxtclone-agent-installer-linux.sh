#!/bin/bash

# SysWatch Agent Installer for Linux
# Single file installer that includes the agent

set -e

INSTALL_DIR="/opt/syswatch"
SERVICE_NAME="syswatch-agent"
AGENT_USER="syswatch"

echo "SysWatch Agent Installer for Linux"
echo "=================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Get server URL
if [ -z "$1" ]; then
    read -p "Enter server URL (e.g., ws://192.168.1.100:3000): " SERVER_URL
else
    SERVER_URL="$1"
fi

if [ -z "$SERVER_URL" ]; then
    echo "Server URL is required"
    exit 1
fi

echo "Installing SysWatch Agent..."
echo "Server URL: $SERVER_URL"

# Create user
if ! id "$AGENT_USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$INSTALL_DIR" "$AGENT_USER"
    echo "Created user: $AGENT_USER"
fi

# Create install directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Extract embedded agent files (this will be replaced by build script)
cat << 'AGENT_FILES_END' | base64 -d | tar -xz
__AGENT_FILES_BASE64__
AGENT_FILES_END

# Set permissions
chown -R "$AGENT_USER:$AGENT_USER" "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/syswatch-agent-linux"

# Create systemd service
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=SysWatch Agent
After=network.target
Wants=network.target

[Service]
Type=simple
User=$AGENT_USER
Group=$AGENT_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/syswatch-agent-linux $SERVER_URL
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

echo ""
echo "Installation completed successfully!"
echo "Service: $SERVICE_NAME"
echo "Status: systemctl status $SERVICE_NAME"
echo "Logs: journalctl -u $SERVICE_NAME -f"
echo ""
echo "The agent is now running and will start automatically on boot."
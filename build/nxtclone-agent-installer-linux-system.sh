#!/bin/bash

# SysWatch Agent System Installer for Linux
# Creates system service that runs for all users

set -e

INSTALL_DIR="/opt/syswatch"
SERVICE_NAME="syswatch-agent"
AGENT_USER="syswatch"

echo "SysWatch Agent System Installer for Linux"
echo "=========================================="
echo "This will install SysWatch as a system service (requires sudo)"

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

# Ask about control app installation
INSTALL_CONTROL="n"
if [ -f "syswatch/syswatch-control" ]; then
    read -p "Install control application for GUI/CLI management? (y/n) [y]: " INSTALL_CONTROL
    INSTALL_CONTROL=${INSTALL_CONTROL:-y}
fi

echo "Installing SysWatch Agent as system service..."
echo "Server URL: $SERVER_URL"

# Create dedicated user for service
if ! id "$AGENT_USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$INSTALL_DIR" "$AGENT_USER"
    echo "Created service user: $AGENT_USER"
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

# Install control app if requested
if [ "$INSTALL_CONTROL" = "y" ] && [ -f "$INSTALL_DIR/syswatch-control" ]; then
    chmod +x "$INSTALL_DIR/syswatch-control"
    # Create symlink in /usr/local/bin for system-wide access
    ln -sf "$INSTALL_DIR/syswatch-control" /usr/local/bin/syswatch-control
    echo "Control app installed: run 'syswatch-control' from anywhere"
fi

# Stop existing service if running
systemctl stop $SERVICE_NAME 2>/dev/null || true
systemctl disable $SERVICE_NAME 2>/dev/null || true

# Create systemd system service
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

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF

# Enable and start system service
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

# Verify service started
sleep 2
if systemctl is-active --quiet $SERVICE_NAME; then
    SERVICE_STATUS="✓ Running"
else
    SERVICE_STATUS="✗ Failed to start"
fi

echo ""
echo "Installation completed!"
echo "======================"
echo "Service: $SERVICE_NAME ($SERVICE_STATUS)"
echo "Install Path: $INSTALL_DIR"
echo "Service User: $AGENT_USER"
echo "Server URL: $SERVER_URL"
echo ""
echo "Management Commands:"
echo "  Status: systemctl status $SERVICE_NAME"
echo "  Logs: journalctl -u $SERVICE_NAME -f"
echo "  Restart: systemctl restart $SERVICE_NAME"
if [ "$INSTALL_CONTROL" = "y" ] && [ -f "$INSTALL_DIR/syswatch-control" ]; then
    echo "  Control app: syswatch-control"
fi
echo ""
echo "The agent is now running as a system service and will start automatically on boot."
echo "It will run independently of user logins and logouts."
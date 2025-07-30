#!/bin/bash

# SysWatch Agent Installer for Linux
# Single file installer that includes the agent

set -e

INSTALL_DIR="$HOME/.local/share/SysWatch"
SERVICE_NAME="syswatch-agent"
CONFIG_DIR="$HOME/.config/SysWatch"

echo "SysWatch Agent Installer for Linux"
echo "=================================="
echo "Installing to user directory (no root required)"

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

echo "Installing SysWatch Agent..."
echo "Server URL: $SERVER_URL"

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$HOME/.config/systemd/user"
cd "$INSTALL_DIR"

# Extract embedded agent files (this will be replaced by build script)
cat << 'AGENT_FILES_END' | base64 -d | tar -xz
__AGENT_FILES_BASE64__
AGENT_FILES_END

# Set permissions
chmod +x "$INSTALL_DIR/syswatch-agent-linux"

# Install control app if requested
if [ "$INSTALL_CONTROL" = "y" ] && [ -f "$INSTALL_DIR/syswatch-control" ]; then
    chmod +x "$INSTALL_DIR/syswatch-control"
    # Create symlink in ~/.local/bin for easy access
    mkdir -p "$HOME/.local/bin"
    ln -sf "$INSTALL_DIR/syswatch-control" "$HOME/.local/bin/syswatch-control"
    echo "Control app installed: add ~/.local/bin to PATH or run '$HOME/.local/bin/syswatch-control'"
fi

# Create user systemd service
cat > "$HOME/.config/systemd/user/$SERVICE_NAME.service" << EOF
[Unit]
Description=SysWatch Agent
After=network.target
Wants=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/syswatch-agent-linux $SERVER_URL
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

# Enable and start user service
systemctl --user daemon-reload
systemctl --user enable $SERVICE_NAME
systemctl --user start $SERVICE_NAME

# Enable lingering so service starts on boot
sudo loginctl enable-linger "$USER"

echo ""
echo "Installation completed successfully!"
echo "Service: $SERVICE_NAME"
echo "Status: systemctl --user status $SERVICE_NAME"
echo "Logs: journalctl --user -u $SERVICE_NAME -f"
if [ "$INSTALL_CONTROL" = "y" ] && [ -f "$INSTALL_DIR/syswatch-control" ]; then
    echo "Control app: syswatch-control"
fi
echo ""
echo "The agent is now running and will start automatically on boot."
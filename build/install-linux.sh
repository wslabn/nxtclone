#!/bin/bash

# NxtClone Agent Linux Installer

INSTALL_DIR="/opt/nxtclone"
SERVICE_FILE="/etc/systemd/system/nxtclone-agent.service"

echo "Installing NxtClone Agent..."

# Create install directory
sudo mkdir -p $INSTALL_DIR

# Copy executable
sudo cp dist/nxtclone-agent $INSTALL_DIR/
sudo chmod +x $INSTALL_DIR/nxtclone-agent

# Create systemd service
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=NxtClone Agent
After=network.target

[Service]
Type=simple
User=root
ExecStart=$INSTALL_DIR/nxtclone-agent
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable nxtclone-agent
sudo systemctl start nxtclone-agent

echo "NxtClone Agent installed and started successfully!"
echo "Status: sudo systemctl status nxtclone-agent"
echo "Logs: sudo journalctl -u nxtclone-agent -f"
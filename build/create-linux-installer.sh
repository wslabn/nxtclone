#!/bin/bash

# Script to create single Linux installer with embedded agent

set -e

echo "Creating single Linux installer..."

# Check if agent executable exists
if [ ! -f "dist/syswatch-agent" ]; then
    echo "Error: dist/syswatch-agent not found"
    echo "Run build-linux.sh first"
    exit 1
fi

# Create temp directory with agent files
TEMP_DIR=$(mktemp -d)
mkdir -p "$TEMP_DIR/syswatch"

# Copy agent files
cp dist/syswatch-agent "$TEMP_DIR/syswatch/"
# Rename for installer compatibility
mv "$TEMP_DIR/syswatch/syswatch-agent" "$TEMP_DIR/syswatch/syswatch-agent-linux"
cp ../agents/*.py "$TEMP_DIR/syswatch/"
cp ../agents/version.txt "$TEMP_DIR/syswatch/"

# Create tar.gz and encode to base64
cd "$TEMP_DIR"
tar -czf agent-files.tar.gz syswatch/
AGENT_FILES_BASE64=$(base64 -w 0 agent-files.tar.gz)

# Create final installer
cd - > /dev/null
cp nxtclone-agent-installer-linux.sh dist/syswatch-agent-installer-linux
sed -i "s/__AGENT_FILES_BASE64__/$AGENT_FILES_BASE64/" dist/syswatch-agent-installer-linux
chmod +x dist/syswatch-agent-installer-linux

# Cleanup
rm -rf "$TEMP_DIR"

echo "Created: dist/syswatch-agent-installer-linux"
echo "Usage: sudo ./syswatch-agent-installer-linux ws://server:3000"
#!/bin/bash

# Script to create single Linux installer with embedded agent

set -e

echo "Creating single Linux installer..."

# Check if agent executable exists
if [ ! -f "dist/syswatch-agent-linux" ]; then
    echo "Error: dist/syswatch-agent-linux not found"
    echo "Run build-linux.py first"
    exit 1
fi

# Create temp directory with agent files
TEMP_DIR=$(mktemp -d)
mkdir -p "$TEMP_DIR/syswatch"

# Copy agent files
cp dist/syswatch-agent-linux "$TEMP_DIR/syswatch/"

# Copy control app if it exists
if [ -f "dist/syswatch-control" ]; then
    cp dist/syswatch-control "$TEMP_DIR/syswatch/"
    echo "Including control app in installer"
fi

cp ../agents/*.py "$TEMP_DIR/syswatch/"
cp ../agents/version.txt "$TEMP_DIR/syswatch/"

# Create tar.gz and encode to base64
cd "$TEMP_DIR"
tar -czf agent-files.tar.gz syswatch/
AGENT_FILES_BASE64=$(base64 -w 0 agent-files.tar.gz)

# Create final installer
cd - > /dev/null
cp nxtclone-agent-installer-linux.sh dist/syswatch-agent-installer-linux

# Use printf instead of sed for large data
printf '%s\n' "$AGENT_FILES_BASE64" > /tmp/agent_data.b64
awk '/^__AGENT_FILES_BASE64__$/ {system("cat /tmp/agent_data.b64"); next} 1' nxtclone-agent-installer-linux.sh > dist/syswatch-agent-installer-linux
rm /tmp/agent_data.b64

chmod +x dist/syswatch-agent-installer-linux

# Cleanup
rm -rf "$TEMP_DIR"

# Ensure installer has correct name
echo "Linux installer created: dist/syswatch-agent-installer-linux"

echo "Created: dist/syswatch-agent-installer-linux"
echo "Usage: sudo ./syswatch-agent-installer-linux ws://server:3000"
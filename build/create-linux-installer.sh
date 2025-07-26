#!/bin/bash

# Script to create single Linux installer with embedded agent

set -e

echo "Creating single Linux installer..."

# Check if agent executable exists
if [ ! -f "dist/nxtclone-agent-linux" ]; then
    echo "Error: dist/nxtclone-agent-linux not found"
    echo "Run build-linux.sh first"
    exit 1
fi

# Create temp directory with agent files
TEMP_DIR=$(mktemp -d)
mkdir -p "$TEMP_DIR/nxtclone"

# Copy agent files
cp dist/nxtclone-agent-linux "$TEMP_DIR/nxtclone/"
cp ../agents/*.py "$TEMP_DIR/nxtclone/"
cp ../agents/version.txt "$TEMP_DIR/nxtclone/"

# Create tar.gz and encode to base64
cd "$TEMP_DIR"
tar -czf agent-files.tar.gz nxtclone/
AGENT_FILES_BASE64=$(base64 -w 0 agent-files.tar.gz)

# Create final installer
cd - > /dev/null
cp nxtclone-agent-installer-linux.sh dist/nxtclone-agent-installer-linux
sed -i "s/__AGENT_FILES_BASE64__/$AGENT_FILES_BASE64/" dist/nxtclone-agent-installer-linux
chmod +x dist/nxtclone-agent-installer-linux

# Cleanup
rm -rf "$TEMP_DIR"

echo "Created: dist/nxtclone-agent-installer-linux"
echo "Usage: sudo ./nxtclone-agent-installer-linux ws://server:3000"
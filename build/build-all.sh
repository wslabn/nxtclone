#!/bin/bash

echo "Building NxtClone Agent Executables..."

# Install build dependencies
pip3 install -r requirements-build.txt

# Build Linux executable
echo "Building Linux agent..."
python3 build-linux.py

# Make installer executable
chmod +x install-linux.sh

echo "Build complete!"
echo "Linux executable: dist/nxtclone-agent"
echo "Linux installer: install-linux.sh"
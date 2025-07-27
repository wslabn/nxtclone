#!/bin/bash

echo "Building NxtClone Agent Executables..."

# Install build dependencies
pip3 install -r requirements-build.txt

# Build Linux executable
echo "Building Linux agent..."
python3 build-linux.py

echo "Build complete!"
echo "Linux executable: dist/syswatch-agent"
echo "Linux installer: dist/syswatch-agent-installer-linux"
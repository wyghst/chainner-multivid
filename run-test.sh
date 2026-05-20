#!/usr/bin/env bash
set -e

echo "=== chainner-multivid test launcher ==="
echo ""

# Check Node.js
if ! command -v node &>/dev/null; then
    echo "ERROR: Node.js not found."
    echo "Install it from https://nodejs.org  (LTS recommended)"
    exit 1
fi
echo "Node.js $(node --version) found."

# Pull latest from git
echo ""
echo "Pulling latest changes..."
git pull origin update/dependencies || echo "WARNING: git pull failed. Continuing with local files."

# Install / sync dependencies
echo ""
echo "Syncing dependencies..."
npm install --legacy-peer-deps

echo ""
echo "Starting chainner-multivid..."
echo "(The app window will open. Close it or Ctrl+C here to stop.)"
echo ""

npm start

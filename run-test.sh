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

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo ""
    echo "node_modules not found — running npm install..."
    npm install
fi

echo ""
echo "Starting chainner-multivid..."
echo "(The app window will open. Close it or Ctrl+C here to stop.)"
echo ""

npm start

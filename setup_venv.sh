#!/bin/bash
# Setup script for wss virtual environment

cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "wss-venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv wss-venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source wss-venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install --upgrade pip

echo "Setup complete! To activate the virtual environment, run:"
echo "  source wss-venv/bin/activate"
echo ""
echo "Then run the service with:"
echo "  python dev_ws_service.py"


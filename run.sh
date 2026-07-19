#!/bin/bash
cd "$(dirname "$0")"
echo "Installing dependencies..."
pip install -r requirements.txt -q 2>&1
echo "Starting QA Tool..."
python3 server.py
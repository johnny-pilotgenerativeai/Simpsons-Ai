#!/bin/bash

# Store PID file path
PID_FILE="/tmp/bridge_pid.txt"

# Remove any existing PID file
rm -f "$PID_FILE"

# Open a new gnome-terminal window that activates the venv and runs Bridge.py
cd /home/johnny/python/Simpsons-Ai/ || exit
export BRIDGE_PID_FILE="$PID_FILE"
gnome-terminal -- bash -c 'source .venv/bin/activate && python3 Bridge.py & echo $! > "$BRIDGE_PID_FILE"; exec bash'

# In the current window, wait 1 second then run SpringfieldChat.py
sleep 1
source .venv/bin/activate
python3 SpringfieldChat.py

# After SpringfieldChat.py finishes, kill Bridge.py
if [ -f "$PID_FILE" ]; then
    BRIDGE_PID=$(cat "$PID_FILE")
    kill "$BRIDGE_PID" 2>/dev/null
    rm -f "$PID_FILE"
fi

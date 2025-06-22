#!/bin/bash

# Display system information
echo "=== System Information ==="
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "User: $(whoami)"
echo "OS: $(uname -s)"
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo ""
echo "=== Directory Info ==="
echo "Current directory: $(pwd)"
echo "Directory size: $(du -sh . 2>/dev/null | cut -f1)"
echo "Free disk space: $(df -h . | tail -1 | awk '{print $4}')"
echo ""
echo "=== Process Info ==="
echo "Process ID: $$"
echo "Running processes: $(ps aux | wc -l)"
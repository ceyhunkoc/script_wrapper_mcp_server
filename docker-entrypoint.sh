#!/bin/bash
set -e

# MCP Script Runner Docker Entrypoint

echo "🐳 Starting MCP Script Runner in Docker..."

# Set Python path
export PYTHONPATH="/workspace/src:$PYTHONPATH"

# Check if configuration exists, create default if not
if [ ! -f "/workspace/.mcp-config.json" ]; then
    echo "📝 Creating default configuration..."
    cat > /workspace/.mcp-config.json << 'EOF'
{
  "working_directory": "/workspace",
  "scripts": {},
  "docker_image": "ubuntu:22.04",
  "container_name": "mcp-script-runner",
  "mount_path": "/workspace"
}
EOF
fi

# Create scripts directory if it doesn't exist
mkdir -p /workspace/scripts

# Check if any arguments were passed
if [ $# -eq 0 ]; then
    echo "🚀 Starting MCP Script Runner Server..."
    exec python3.11 -m mcp_script_runner.server
else
    # Execute the provided command
    exec "$@"
fi
# MCP Script Runner - Docker Guide

This guide covers how to run the MCP Script Runner as a Docker container.

## Prerequisites

- Docker Engine 20.10+ or Docker Desktop
- Docker Compose V2 (comes with modern Docker installations)

## Quick Start

### 1. Build and Run with Docker Compose

```bash
# Build and start the container
docker compose up --build -d

# Check logs
docker compose logs -f

# Stop the container
docker compose down
```

### 2. Direct Docker Commands

```bash
# Build the image
docker build -t mcp-script-runner .

# Run the container
docker run --rm -it \
  -v $(pwd):/workspace \
  --name mcp-script-runner \
  mcp-script-runner

# Run with custom working directory
docker run --rm -it \
  -v /path/to/your/project:/workspace \
  --name mcp-script-runner \
  mcp-script-runner
```

## Container Features

### Included Tools
- **Python 3.11** - Runtime environment
- **Bash** - Shell for script execution
- **Git** - Version control
- **Build essentials** - Compilers and development tools
- **curl/wget** - Network utilities

### Default Configuration
- **Working Directory**: `/workspace`
- **User**: `mcpuser` (non-root)
- **Python Path**: `/workspace/src`
- **Scripts Directory**: `/workspace/scripts`

## Usage Examples

### Interactive Shell
```bash
# Start an interactive shell session
docker compose run --rm mcp-script-runner bash

# Or with direct docker command
docker run --rm -it -v $(pwd):/workspace mcp-script-runner bash
```

### Debug Mode
```bash
# Use the debug shell service
docker compose --profile debug up shell

# Interactive debug session
docker compose run --rm shell
```

### Testing Scripts
```bash
# Test a script inside the container
docker run --rm -v $(pwd):/workspace mcp-script-runner \
  python3.11 -c "
import sys; sys.path.insert(0, 'src')
from mcp_script_runner.executor import ScriptExecutor
from mcp_script_runner.config import ConfigManager
import asyncio

cm = ConfigManager()
ex = ScriptExecutor(cm)
result = asyncio.run(ex.execute_script('hello'))
print(f'Exit code: {result.exit_code}')
print(result.stdout)
"
```

## Configuration

### Mount Points
The container expects your project to be mounted at `/workspace`. This includes:
- **Scripts**: Place in `./scripts/` directory
- **Configuration**: `.mcp-config.json` in project root
- **Source Code**: MCP server code in `./src/`

### Environment Variables
```bash
# Custom Python path
-e PYTHONPATH=/workspace/src:/custom/path

# Enable debug logging
-e PYTHONUNBUFFERED=1

# Terminal compatibility
-e TERM=xterm-256color
```

### Volume Mounts
```bash
# Mount current directory
-v $(pwd):/workspace

# Mount specific project directory
-v /path/to/project:/workspace

# Mount additional directories
-v /additional/scripts:/workspace/additional
```

## Docker Compose Services

### Main Service: `mcp-script-runner`
```yaml
services:
  mcp-script-runner:
    # Main MCP server container
    # Starts automatically and waits for MCP client connections
```

### Debug Service: `shell`
```yaml
services:
  shell:
    # Interactive shell for debugging
    # Use: docker compose --profile debug up shell
```

## Production Deployment

### Running as MCP Server
```bash
# Start the server and keep it running
docker compose up -d

# Connect from MCP client
# The server listens on stdio for MCP protocol messages
```

### Health Checks
```bash
# Check if container is running
docker compose ps

# View logs
docker compose logs -f mcp-script-runner

# Test server functionality
docker compose exec mcp-script-runner python3.11 -c "
import sys; sys.path.insert(0, 'src')
from mcp_script_runner.config import ConfigManager
cm = ConfigManager()
print('✅ Server healthy')
"
```

## Development Workflow

### 1. Develop Locally
```bash
# Start development environment
docker compose --profile debug up shell

# Inside container, test changes
python3.11 -m mcp_script_runner.server
```

### 2. Build and Test
```bash
# Rebuild after changes
docker compose up --build

# Test script execution
docker compose exec mcp-script-runner \
  python3.11 -c "from src.mcp_script_runner.executor import ScriptExecutor; print('OK')"
```

### 3. Deploy
```bash
# Production deployment
docker compose up -d

# Monitor
docker compose logs -f
```

## Troubleshooting

### Container Won't Start
```bash
# Check build logs
docker compose up --build

# Run with debug
docker compose run --rm mcp-script-runner bash
```

### Script Execution Issues
```bash
# Check file permissions
docker compose exec mcp-script-runner ls -la scripts/

# Test script directly
docker compose exec mcp-script-runner bash scripts/hello.sh
```

### MCP Server Issues
```bash
# Check server logs
docker compose logs mcp-script-runner

# Test server import
docker compose exec mcp-script-runner python3.11 -c "
import sys; sys.path.insert(0, 'src')
from mcp_script_runner.server import main
print('✅ Server imports OK')
"
```

### Permission Issues
```bash
# Check user permissions
docker compose exec mcp-script-runner whoami
docker compose exec mcp-script-runner id

# Fix file ownership (if needed)
sudo chown -R $(id -u):$(id -g) .
```

## Best Practices

### Security
- ✅ Container runs as non-root user (`mcpuser`)
- ✅ Only necessary ports exposed
- ✅ Minimal base image (Ubuntu 22.04)
- ⚠️ Mount only required directories
- ⚠️ Avoid mounting Docker socket unless needed

### Performance
- ✅ Use `.dockerignore` to exclude unnecessary files
- ✅ Multi-stage builds for optimized images
- ✅ Layer caching for faster rebuilds
- ⚠️ Consider resource limits for production

### Maintenance
- 🔄 Regular image updates
- 🔄 Monitor container logs
- 🔄 Backup mounted volumes
- 🔄 Test script execution regularly

## Advanced Usage

### Custom Base Image
```dockerfile
# Create custom image with additional tools
FROM devmcp-mcp-script-runner:latest
RUN apt-get update && apt-get install -y your-tools
```

### Multiple Projects
```bash
# Run multiple instances for different projects
docker run --rm -d \
  -v /project1:/workspace \
  --name mcp-project1 \
  mcp-script-runner

docker run --rm -d \
  -v /project2:/workspace \
  --name mcp-project2 \
  mcp-script-runner
```

### Resource Limits
```yaml
services:
  mcp-script-runner:
    # ... other config
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

## Integration Examples

### With Claude Desktop
```json
{
  "mcpServers": {
    "script-runner": {
      "command": "docker",
      "args": [
        "compose", "-f", "/path/to/devmcp/docker-compose.yml",
        "run", "--rm", "mcp-script-runner"
      ]
    }
  }
}
```

### With Custom MCP Client
```python
# Example client connection
import subprocess
import json

# Start container
process = subprocess.Popen([
    "docker", "compose", "run", "--rm", "mcp-script-runner"
], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

# Send MCP messages
message = {"method": "tools/list"}
process.stdin.write(json.dumps(message) + "\n")
response = process.stdout.readline()
```

---

## Summary

The MCP Script Runner Docker container provides:
- ✅ Isolated execution environment
- ✅ Consistent runtime across systems
- ✅ Easy deployment and scaling
- ✅ Development and production ready
- ✅ Comprehensive tooling included

Start with `docker compose up --build` and you're ready to go!
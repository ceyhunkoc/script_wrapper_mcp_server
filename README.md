# MCP Script Runner

A Model Context Protocol (MCP) server that provides coding agents with a generic interface to execute developer-defined bash scripts within a Dockerized environment.

## 🚀 Quick Start

### Option 1: Docker (Recommended)
```bash
# Clone and run with Docker
git clone <repository-url>
cd devmcp
docker compose up --build -d

# Check logs
docker compose logs -f
```

### Option 2: Local Installation
```bash
# Clone repository
git clone <repository-url>
cd devmcp

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m mcp_script_runner.server
```

## 📋 Overview

The MCP Script Runner Server enables AI agents to:
- **Execute predefined bash scripts** with configurable arguments
- **Manage working directories** for different project contexts
- **Get script information** including descriptions and available arguments
- **List available scripts** dynamically
- **Handle script timeouts** and error conditions gracefully

## 🐳 Docker Support

The project includes full Docker support for containerized execution:

- **🔧 Ready-to-use containers** with all dependencies
- **🛡️ Isolated execution environment**
- **📦 Easy deployment** with Docker Compose
- **🔍 Debug capabilities** with interactive shell access

See **[DOCKER.md](./DOCKER.md)** for complete Docker usage guide.

### Quick Docker Commands
```bash
# Start the MCP server
docker compose up --build -d

# Interactive development shell
docker compose --profile debug up shell

# Test script execution
docker compose exec mcp-script-runner bash scripts/hello.sh
```

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- Docker (for containerized execution)
- Bash-compatible shell

### Local Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "from src.mcp_script_runner.server import main; print('✅ Installation OK')"
```

### Docker Setup
```bash
# Build container
docker build -t mcp-script-runner .

# Or use Docker Compose
docker compose up --build
```

## ⚙️ Configuration

### Configuration File: `.mcp-config.json`
```json
{
  "working_directory": ".",
  "scripts": {
    "hello": {
      "path": "scripts/hello.sh",
      "description": "Simple hello world script",
      "arguments": [],
      "timeout": 30
    },
    "list_files": {
      "path": "scripts/list_files.sh",
      "description": "List files in directory with options",
      "arguments": ["directory", "options"],
      "timeout": 10
    }
  }
}
```

### Script Directory Structure
```
project/
├── .mcp-config.json
├── scripts/
│   ├── hello.sh
│   ├── list_files.sh
│   └── system_info.sh
└── src/
    └── mcp_script_runner/
```

## 🔧 Available MCP Tools

| Tool | Description | Arguments |
|------|-------------|-----------|
| `run_script` | Execute a configured script | `script_name`, `arguments[]` |
| `list_scripts` | List all available scripts | None |
| `get_script_info` | Get script details | `script_name` |
| `get_working_directory` | Get current working directory | None |
| `set_working_directory` | Set working directory | `path` |
| `reload_config` | Reload configuration file | None |

### Example Tool Usage
```json
{
  "tool": "run_script",
  "arguments": {
    "script_name": "hello",
    "arguments": []
  }
}
```

## 🏃‍♂️ Running the Server

### Local Execution
```bash
# Start MCP server (listens on stdio)
python -m mcp_script_runner.server

# Or with explicit path
PYTHONPATH=src python -m mcp_script_runner.server
```

### Docker Execution
```bash
# Background service
docker compose up -d

# Interactive mode
docker compose run --rm mcp-script-runner

# Debug shell
docker compose --profile debug up shell
```

## 📝 Example Scripts

### Basic Hello Script (`scripts/hello.sh`)
```bash
#!/bin/bash
echo "Hello from MCP Script Runner!"
echo "Current directory: $(pwd)"
echo "Script arguments: $@"
echo "Date: $(date)"
```

### File Listing Script (`scripts/list_files.sh`)
```bash
#!/bin/bash
DIRECTORY=${1:-.}
OPTIONS=${2:-"-la"}
echo "Listing files in: $DIRECTORY"
ls $OPTIONS "$DIRECTORY"
```

### System Info Script (`scripts/system_info.sh`)
```bash
#!/bin/bash
echo "=== System Information ==="
echo "OS: $(uname -s)"
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo "Uptime: $(uptime)"
echo "Disk Usage:"
df -h
```

## 🧪 Testing

### Unit Tests
```bash
# Run tests locally
python -m pytest tests/

# Run tests in Docker
docker compose run --rm mcp-script-runner python -m pytest tests/
```

### Manual Testing
```bash
# Test script execution
python -c "
import asyncio
from src.mcp_script_runner.executor import ScriptExecutor
from src.mcp_script_runner.config import ConfigManager

async def test():
    cm = ConfigManager()
    ex = ScriptExecutor(cm)
    result = await ex.execute_script('hello')
    print(f'Exit code: {result.exit_code}')
    print(result.stdout)

asyncio.run(test())
"
```

## 🔐 Security Considerations

- **🛡️ Containerized execution** isolates script execution
- **👤 Non-root user** inside containers (`mcpuser`)
- **📁 Limited file access** through volume mounts
- **⏱️ Script timeouts** prevent runaway processes
- **🚫 No shell injection** - arguments passed safely

## 🎯 Use Cases

### Development Automation
- Build and test commands
- Code generation scripts
- Development environment setup

### System Administration
- System monitoring scripts
- Backup and maintenance tasks
- Configuration management

### CI/CD Integration
- Deployment scripts
- Environment validation
- Automated testing workflows

### Project Management
- Task automation
- Report generation
- Resource management

## 🐛 Troubleshooting

### Common Issues

**MCP Server Won't Start**
```bash
# Check Python path
export PYTHONPATH=src

# Verify dependencies
pip install -r requirements.txt

# Check configuration
python -c "from src.mcp_script_runner.config import ConfigManager; cm = ConfigManager(); print('Config OK')"
```

**Script Execution Fails**
```bash
# Check script permissions
chmod +x scripts/*.sh

# Test script directly
bash scripts/hello.sh

# Check Docker logs
docker compose logs mcp-script-runner
```

**Docker Issues**
```bash
# Rebuild container
docker compose up --build

# Check container status
docker compose ps

# Interactive debugging
docker compose run --rm mcp-script-runner bash
```

### Debug Mode
```bash
# Local debug
PYTHONPATH=src python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from mcp_script_runner.server import main
import asyncio
asyncio.run(main())
"

# Docker debug
docker compose --profile debug up shell
```

## 📚 Development

### Project Structure
```
devmcp/
├── 📄 README.md              # This file
├── 🐳 DOCKER.md              # Docker usage guide
├── 📋 TASKS.md               # Development tasks
├── ⚙️ .mcp-config.json       # Configuration
├── 🐳 Dockerfile             # Container definition
├── 🐳 docker-compose.yml     # Container orchestration
├── 📦 requirements.txt       # Python dependencies
├── 📦 pyproject.toml         # Python project config
├── 🔧 scripts/               # Example scripts
├── 🐍 src/mcp_script_runner/ # Python source code
└── 🧪 tests/                 # Unit tests
```

### Adding New Scripts
1. Create script in `scripts/` directory
2. Make executable: `chmod +x scripts/myscript.sh`
3. Add to `.mcp-config.json`:
```json
{
  "scripts": {
    "myscript": {
      "path": "scripts/myscript.sh",
      "description": "My custom script",
      "arguments": ["arg1", "arg2"],
      "timeout": 30
    }
  }
}
```
4. Reload configuration: Use `reload_config` tool

### Contributing
1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Test with Docker: `docker compose up --build`
5. Submit pull request

## 🚀 Deployment

### Production Deployment
```bash
# Using Docker Compose
docker compose up -d

# Using Docker Swarm
docker stack deploy -c docker-compose.yml mcp-stack

# Using Kubernetes
kubectl apply -f k8s/
```

### Integration with MCP Clients

**Claude Desktop Configuration**
```json
{
  "mcpServers": {
    "script-runner": {
      "command": "docker",
      "args": ["compose", "-f", "/path/to/devmcp/docker-compose.yml", "run", "--rm", "mcp-script-runner"]
    }
  }
}
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Support

- 📖 Documentation: See [DOCKER.md](./DOCKER.md) for Docker usage
- 🐛 Issues: Create GitHub issue
- 💬 Discussions: GitHub Discussions
- 📧 Contact: See repository contributors

---

**Ready to get started?**

🐳 **Docker users**: `docker compose up --build`
🐍 **Local users**: `pip install -r requirements.txt && python -m mcp_script_runner.server`
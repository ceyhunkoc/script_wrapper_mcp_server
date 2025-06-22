# MCP Script Runner Server - Planning Document

## Project Overview

A Model Context Protocol (MCP) server that provides coding agents with a generic interface to execute developer-defined bash scripts within a Dockerized environment. The server acts as a bridge between AI agents and project-specific tooling.

## Core Vision

- **Generic & Portable**: Works across different projects and languages without modification
- **Developer-Controlled**: All project logic lives in bash scripts written by developers
- **Simple Interface**: Clean MCP tools that wrap script execution
- **Containerized**: Runs in Docker for consistent environments

## Scope

### In Scope
- Execute bash scripts defined in project configuration
- Return stdout/stderr/exit codes to agents
- Basic script discovery and listing
- Docker container management
- Single-agent, local development usage
- Language-agnostic design

### Out of Scope (v1)
- Multi-agent support
- Sandboxing/security isolation
- Complex error handling/recovery
- Script parameter validation
- Authentication/authorization
- Remote deployment
- GUI/web interface

## Technical Architecture

### Execution Model
- **Container Strategy**: Single container approach (Option 1)
- **Server Location**: MCP server runs inside Docker container
- **Script Execution**: All scripts execute within the same container environment
- **File Access**: Project files mounted as Docker volumes
- **State**: Long-running container maintains state between script executions

### Technology Stack
- **Language**: Python (for MCP server implementation)
- **MCP Library**: `mcp` Python package
- **Container**: Docker with Python base image
- **Protocol**: MCP (Model Context Protocol)
- **Configuration**: JSON-based script definitions
- **Scripts**: Bash (developer-provided)

### Container Design
- Base Ubuntu image with common development tools
- Pre-installed runtimes: Python, Node.js, Go
- Project files mounted to `/workspace`
- Server runs on port 8080
- Persistent container for multiple script executions

## Key Design Principles

1. **Simplicity First**: Minimal abstraction over bash execution
2. **Developer Control**: Scripts contain all project-specific logic
3. **Zero Configuration**: Works out of the box with sensible defaults
4. **Extensible**: Easy to add new tools and customize container
5. **Transparent**: Direct access to stdout/stderr for debugging

## Success Criteria

- Agent can discover available scripts in any project
- Agent can execute scripts and receive full output
- Container startup time under 5 seconds
- Scripts execute with proper working directory context
- Project files accessible and modifiable from scripts
- Easy onboarding for new projects (just add config + scripts)

## Future Considerations

- Support for script-specific container images
- Built-in common development tools (linting, formatting)
- Integration with popular CI/CD patterns
- Performance optimizations for large projects
- Multi-language template generators

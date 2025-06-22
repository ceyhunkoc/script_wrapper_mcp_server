"""MCP Script Runner Server."""

import asyncio
import logging
from typing import Any, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config import ConfigManager
from .executor import ScriptExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server
server = Server("mcp-script-runner")

# Global instances
config_manager = ConfigManager()
script_executor = ScriptExecutor(config_manager)


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="run_script",
            description="Execute a configured bash script",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_name": {
                        "type": "string",
                        "description": "Name of the script to execute"
                    },
                    "arguments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Arguments to pass to the script"
                    }
                },
                "required": ["script_name"]
            }
        ),
        Tool(
            name="list_scripts",
            description="List all available scripts",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_script_info",
            description="Get detailed information about a specific script",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_name": {
                        "type": "string",
                        "description": "Name of the script to get info for"
                    }
                },
                "required": ["script_name"]
            }
        ),
        Tool(
            name="get_working_directory",
            description="Get the current working directory",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="set_working_directory",
            description="Set the working directory for script execution",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to set as working directory"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="reload_config",
            description="Reload configuration from file",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls."""
    try:
        if name == "run_script":
            return await handle_run_script(arguments)
        elif name == "list_scripts":
            return await handle_list_scripts(arguments)
        elif name == "get_script_info":
            return await handle_get_script_info(arguments)
        elif name == "get_working_directory":
            return await handle_get_working_directory(arguments)
        elif name == "set_working_directory":
            return await handle_set_working_directory(arguments)
        elif name == "reload_config":
            return await handle_reload_config(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_run_script(arguments: dict) -> List[TextContent]:
    """Handle script execution."""
    script_name = arguments.get("script_name")
    script_arguments = arguments.get("arguments", [])

    if not script_name:
        return [TextContent(type="text", text="Error: script_name is required")]

    try:
        result = await script_executor.execute_script(script_name, script_arguments)

        # Format output
        output_lines = [
            f"Script: {result.script_name}",
            f"Exit Code: {result.exit_code}",
            f"Execution Time: {result.execution_time:.2f}s",
            f"Success: {result.success}",
            "",
            "STDOUT:",
            result.stdout,
            "",
            "STDERR:",
            result.stderr
        ]

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error executing script: {str(e)}")]


async def handle_list_scripts(arguments: dict) -> List[TextContent]:
    """Handle script listing."""
    try:
        scripts = script_executor.list_available_scripts()

        if not scripts:
            return [TextContent(type="text", text="No scripts configured")]

        output_lines = ["Available Scripts:", ""]
        for script in scripts:
            output_lines.extend([
                f"Name: {script['name']}",
                f"Description: {script['description']}",
                f"Path: {script['path']}",
                f"Arguments: {', '.join(script['arguments']) if script['arguments'] else 'None'}",
                f"Timeout: {script['timeout']}s",
                ""
            ])

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error listing scripts: {str(e)}")]


async def handle_get_script_info(arguments: dict) -> List[TextContent]:
    """Handle getting script information."""
    script_name = arguments.get("script_name")

    if not script_name:
        return [TextContent(type="text", text="Error: script_name is required")]

    try:
        script_info = script_executor.get_script_info(script_name)

        if not script_info:
            return [TextContent(type="text", text=f"Script not found: {script_name}")]

        output_lines = [
            f"Script Information: {script_name}",
            "",
            f"Name: {script_info['name']}",
            f"Description: {script_info['description']}",
            f"Path: {script_info['path']}",
            f"Arguments: {', '.join(script_info['arguments']) if script_info['arguments'] else 'None'}",
            f"Timeout: {script_info['timeout']}s",
            f"Working Directory: {script_info['working_directory'] or 'Default'}"
        ]

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error getting script info: {str(e)}")]


async def handle_get_working_directory(arguments: dict) -> List[TextContent]:
    """Handle getting current working directory."""
    try:
        working_dir = config_manager.config.working_directory
        return [TextContent(type="text", text=f"Current working directory: {working_dir}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error getting working directory: {str(e)}")]


async def handle_set_working_directory(arguments: dict) -> List[TextContent]:
    """Handle setting working directory."""
    path = arguments.get("path")

    if not path:
        return [TextContent(type="text", text="Error: path is required")]

    try:
        import os
        if not os.path.exists(path):
            return [TextContent(type="text", text=f"Error: Directory does not exist: {path}")]

        # Update the configuration (this is a simple approach, in practice you might want to persist this)
        config_manager.config.working_directory = path

        return [TextContent(type="text", text=f"Working directory set to: {path}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error setting working directory: {str(e)}")]


async def handle_reload_config(arguments: dict) -> List[TextContent]:
    """Handle configuration reload."""
    try:
        config_manager.reload_config()
        # Reinitialize executor with new config
        global script_executor
        script_executor = ScriptExecutor(config_manager)

        return [TextContent(type="text", text="Configuration reloaded successfully")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error reloading configuration: {str(e)}")]


async def main():
    """Main server entry point."""
    try:
        # Load initial configuration
        config_manager.load_config()
        logger.info("MCP Script Runner Server starting...")

        # Run the server with proper stdio streams
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
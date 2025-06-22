#!/usr/bin/env python3
"""Debug MCP communication"""

import asyncio
import json
import sys
import os
from pathlib import Path

async def debug_mcp():
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{Path.cwd() / 'src'}:{env.get('PYTHONPATH', '')}"
    
    print("🔍 Starting MCP debug session...")
    
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "mcp_script_runner.server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )
    
    await asyncio.sleep(1)
    
    if process.returncode is not None:
        stderr = await process.stderr.read()
        print(f"❌ Server failed: {stderr.decode()}")
        return
    
    print("✅ Server started")
    
    # Initialize
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "debug-client", "version": "1.0.0"}
        }
    }
    
    print(f"📤 Sending: {json.dumps(init_request)}")
    process.stdin.write((json.dumps(init_request) + "\n").encode())
    await process.stdin.drain()
    
    response_line = await process.stdout.readline()
    response = json.loads(response_line.decode().strip())
    print(f"📥 Response: {json.dumps(response, indent=2)}")
    
    # Send initialized notification
    notification = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    
    print(f"📤 Sending notification: {json.dumps(notification)}")
    process.stdin.write((json.dumps(notification) + "\n").encode())
    await process.stdin.drain()
    
    # List tools
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    print(f"📤 Sending: {json.dumps(tools_request)}")
    process.stdin.write((json.dumps(tools_request) + "\n").encode())
    await process.stdin.drain()
    
    response_line = await process.stdout.readline()
    response = json.loads(response_line.decode().strip())
    print(f"📥 Response: {json.dumps(response, indent=2)}")
    
    # Call a tool
    tool_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "get_working_directory",
            "arguments": {}
        }
    }
    
    print(f"📤 Sending: {json.dumps(tool_request)}")
    process.stdin.write((json.dumps(tool_request) + "\n").encode())
    await process.stdin.drain()
    
    response_line = await process.stdout.readline()
    response = json.loads(response_line.decode().strip())
    print(f"📥 Response: {json.dumps(response, indent=2)}")
    
    # Cleanup
    process.terminate()
    await process.wait()
    print("🛑 Server stopped")

asyncio.run(debug_mcp())

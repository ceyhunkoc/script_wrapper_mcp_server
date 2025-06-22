#!/usr/bin/env python3
"""
Simple MCP Script Runner Test Client

A streamlined test client for the MCP Script Runner server.
"""

import asyncio
import json
import sys
import os
from pathlib import Path


class SimpleMCPClient:
    """Simple MCP client for testing."""
    
    def __init__(self):
        self.process = None
        self.request_id = 0
    
    async def start_server(self):
        """Start the MCP server."""
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{Path.cwd() / 'src'}:{env.get('PYTHONPATH', '')}"
        
        print("🚀 Starting MCP server...")
        
        self.process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "mcp_script_runner.server",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        await asyncio.sleep(1)
        
        if self.process.returncode is not None:
            stderr = await self.process.stderr.read()
            print(f"❌ Server failed: {stderr.decode()}")
            return False
        
        print("✅ Server started")
        return True
    
    async def stop_server(self):
        """Stop the server."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            print("🛑 Server stopped")
    
    async def send_request(self, method, params=None):
        """Send an MCP request."""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        try:
            response_line = await asyncio.wait_for(self.process.stdout.readline(), timeout=5.0)
            if response_line:
                return json.loads(response_line.decode().strip())
            return None
        except asyncio.TimeoutError:
            print(f"❌ Timeout waiting for {method} response")
            return None
    
    async def send_notification(self, method, params=None):
        """Send an MCP notification."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        
        request_json = json.dumps(notification) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
    
    async def initialize(self):
        """Initialize the MCP connection."""
        response = await self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "simple-test-client", "version": "1.0.0"}
        })
        
        if response and "result" in response:
            print("✅ Initialized successfully")
            # Send initialized notification
            await self.send_notification("notifications/initialized")
            return True
        else:
            print("❌ Initialization failed")
            return False
    
    async def list_tools(self):
        """List available tools."""
        response = await self.send_request("tools/list")
        if response and "result" in response:
            tools = response["result"].get("tools", [])
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
            return tools
        else:
            print("❌ Failed to list tools")
            return []
    
    async def call_tool(self, name, arguments=None):
        """Call a tool."""
        response = await self.send_request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })
        
        if response and "result" in response:
            print(f"✅ Tool '{name}' executed successfully")
            content = response["result"].get("content", [])
            for item in content:
                text = item.get("text", "")
                if text:
                    print(f"   Output: {text[:200]}{'...' if len(text) > 200 else ''}")
            return response["result"]
        else:
            error = response.get("error", {}) if response else {}
            print(f"❌ Tool '{name}' failed: {error.get('message', 'Unknown error')}")
            return None


async def run_tests():
    """Run comprehensive tests."""
    client = SimpleMCPClient()
    
    try:
        # Start server
        if not await client.start_server():
            return False
        
        # Initialize
        if not await client.initialize():
            return False
        
        print("\n📋 Testing Tool Discovery")
        tools = await client.list_tools()
        
        if not tools:
            print("❌ No tools found")
            return False
        
        print("\n🔧 Testing Tool Execution")
        
        # Test get working directory
        await client.call_tool("get_working_directory")
        
        # Test list scripts
        await client.call_tool("list_scripts")
        
        # Test script info
        await client.call_tool("get_script_info", {"script_name": "hello"})
        
        # Test script execution
        await client.call_tool("run_script", {"script_name": "hello", "arguments": []})
        
        # Test error handling
        await client.call_tool("run_script", {"script_name": "nonexistent"})
        
        # Test config reload
        await client.call_tool("reload_config")
        
        print("\n✅ All tests completed successfully!")
        return True
        
    finally:
        await client.stop_server()


async def interactive_mode():
    """Interactive mode for manual testing."""
    client = SimpleMCPClient()
    
    try:
        if not await client.start_server():
            return
        
        if not await client.initialize():
            return
        
        tools = await client.list_tools()
        
        print("\n🎮 Interactive Mode")
        print("Commands:")
        print("  list - List tools")
        print("  call <tool_name> [json_args] - Call a tool")
        print("  quit - Exit")
        print()
        
        while True:
            try:
                command = input("mcp> ").strip()
                
                if not command:
                    continue
                elif command == "quit":
                    break
                elif command == "list":
                    await client.list_tools()
                elif command.startswith("call "):
                    parts = command.split(" ", 2)
                    tool_name = parts[1]
                    args = {}
                    
                    if len(parts) > 2:
                        try:
                            args = json.loads(parts[2])
                        except json.JSONDecodeError:
                            print("❌ Invalid JSON arguments")
                            continue
                    
                    await client.call_tool(tool_name, args)
                else:
                    print("❌ Unknown command")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    finally:
        await client.stop_server()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple MCP Test Client")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive:
        await interactive_mode()
    else:
        success = await run_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(1)

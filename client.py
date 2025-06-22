#!/usr/bin/env python3
"""
Decoupled MCP Client

Spawns its own server connection but doesn't manage server lifecycle.
The server manager ensures the server is ready to accept connections.
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MCPResponse:
    """Represents an MCP response."""
    success: bool
    data: Any
    error: Optional[str] = None


class MCPClient:
    """MCP client that spawns its own server connection."""

    def __init__(self):
        """Initialize the MCP client."""
        self.process = None
        self.request_id = 0
        self.connected = False

    async def connect(self) -> bool:
        """Connect by spawning a server process."""
        try:
            # Setup environment
            env = os.environ.copy()
            env["PYTHONPATH"] = f"{Path.cwd() / 'src'}:{env.get('PYTHONPATH', '')}"

            print("🔌 Connecting to MCP server...")

            # Spawn server process
            self.process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "mcp_script_runner.server",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            await asyncio.sleep(0.5)

            if self.process.returncode is not None:
                print("❌ Failed to spawn server process")
                return False

            # Initialize the connection
            init_response = await self.initialize()
            if init_response.success:
                self.connected = True
                print("✅ Connected to MCP server")
                return True
            else:
                print(f"❌ Failed to initialize connection: {init_response.error}")
                return False

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
                self.connected = False
                print("🔌 Disconnected from MCP server")
            except Exception as e:
                print(f"⚠️ Error during disconnect: {e}")

    def _get_next_request_id(self) -> int:
        """Get the next request ID."""
        self.request_id += 1
        return self.request_id

    async def send_request(self, method: str, params: Dict[str, Any] = None) -> MCPResponse:
        """Send an MCP request to the server."""
        if not self.process or self.process.returncode is not None:
            return MCPResponse(success=False, error="Not connected to server")

        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": method,
            "params": params or {}
        }
        print(f"Sending request: {json.dumps(request) }")
        try:
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()

            response_line = await asyncio.wait_for(self.process.stdout.readline(), timeout=5.0)
            if not response_line:
                return MCPResponse(success=False, error="No response from server")

            response_data = json.loads(response_line.decode().strip())

            if "error" in response_data:
                return MCPResponse(
                    success=False,
                    data=response_data,
                    error=response_data["error"].get("message", "Unknown error")
                )

            return MCPResponse(success=True, data=response_data.get("result"))

        except asyncio.TimeoutError:
            return MCPResponse(success=False, error="Request timeout")
        except Exception as e:
            return MCPResponse(success=False, error=f"Request failed: {e}")

    async def send_notification(self, method: str, params: Dict[str, Any] = None):
        """Send an MCP notification (no response expected)."""
        if not self.process or self.process.returncode is not None:
            return

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }

        try:
            notification_json = json.dumps(notification) + "\n"
            print(f"Sending notification: {notification_json}")
            self.process.stdin.write(notification_json.encode())
            await self.process.stdin.drain()
        except Exception as e:
            print(f"Warning: Failed to send notification {method}: {e}")

    async def initialize(self) -> MCPResponse:
        """Initialize the MCP connection."""
        response = await self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "mcp-client", "version": "1.0.0"}
        })
        print(f"Initialize response: {response}")
        if response.success:
            # Send required initialized notification
            await self.send_notification("notifications/initialized")

        return response

    async def list_tools(self) -> MCPResponse:
        """List available tools."""
        return await self.send_request("tools/list")

    async def call_tool(self, name: str, arguments: Dict[str, Any] = None) -> MCPResponse:
        """Call a tool."""
        return await self.send_request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })


async def run_tests(client: MCPClient):
    """Run basic tests."""
    print("\n🧪 Running Tests")
    print("=" * 30)

    tests_passed = 0
    tests_total = 0

    # Test 1: List tools
    tests_total += 1
    print("🛠️ Testing tool discovery...")
    response = await client.list_tools()
    if response.success:
        tools = response.data.get("tools", [])
        print(f"✅ Found {len(tools)} tools: {', '.join([t['name'] for t in tools])}")
        tests_passed += 1
    else:
        print(f"❌ Tool discovery failed: {response.error}")

    # Test 2: Get working directory
    tests_total += 1
    print("\n📁 Testing working directory...")
    response = await client.call_tool("get_working_directory")
    if response.success:
        content = response.data.get("content", [])
        if content:
            directory = content[0].get("text", "N/A")
            print(f"✅ Current directory: {directory}")
            tests_passed += 1
        else:
            print("❌ No directory information returned")
    else:
        print(f"❌ Get working directory failed: {response.error}")

    # Test 3: List scripts
    tests_total += 1
    print("\n📜 Testing script listing...")
    response = await client.call_tool("list_scripts")
    if response.success:
        content = response.data.get("content", [])
        if content:
            scripts_text = content[0].get("text", "")
            print(f"✅ Scripts listed successfully")
            print(f"   Preview: {scripts_text[:100]}...")
            tests_passed += 1
        else:
            print("❌ No scripts information returned")
    else:
        print(f"❌ List scripts failed: {response.error}")

    # Test 4: Execute hello script
    tests_total += 1
    print("\n🎯 Testing script execution...")
    response = await client.call_tool("run_script", {
        "script_name": "hello",
        "arguments": []
    })
    if response.success:
        content = response.data.get("content", [])
        if content:
            output = content[0].get("text", "")
            print("✅ Script executed successfully")
            print(f"   Output preview: {output[:150]}...")
            tests_passed += 1
        else:
            print("❌ No script output returned")
    else:
        print(f"❌ Script execution failed: {response.error}")

    # Results
    success_rate = (tests_passed / tests_total * 100) if tests_total > 0 else 0

    print("\n" + "=" * 30)
    print("📊 Test Results")
    print(f"Passed: {tests_passed}/{tests_total}")
    print(f"Success Rate: {success_rate:.1f}%")

    if tests_passed == tests_total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️ {tests_total - tests_passed} test(s) failed")

    return tests_passed == tests_total


async def interactive_mode(client: MCPClient):
    """Interactive mode for manual testing."""
    print("\n🎮 Interactive Mode")
    print("Commands:")
    print("  list - List available tools")
    print("  call <tool_name> [json_args] - Call a tool")
    print("  help - Show this help")
    print("  quit - Exit")
    print()

    while True:
        try:
            command = input("mcp> ").strip()

            if not command:
                continue
            elif command == "quit":
                break
            elif command == "help":
                print("Available commands:")
                print("  list - List available tools")
                print("  call run_script {\"script_name\": \"hello\"}")
                print("  call list_scripts")
                print("  call get_working_directory")
                print("  quit - Exit")
            elif command == "list":
                response = await client.list_tools()
                if response.success:
                    tools = response.data.get("tools", [])
                    print(f"Available tools ({len(tools)}):")
                    for tool in tools:
                        print(f"  📋 {tool['name']}")
                        print(f"     {tool['description']}")
                        print()
                else:
                    print(f"❌ Error: {response.error}")
            elif command.startswith("call "):
                parts = command.split(" ", 2)
                if len(parts) < 2:
                    print("Usage: call <tool_name> [json_args]")
                    continue

                tool_name = parts[1]
                args = {}

                if len(parts) > 2:
                    try:
                        args = json.loads(parts[2])
                    except json.JSONDecodeError as e:
                        print(f"❌ Invalid JSON arguments: {e}")
                        continue

                print(f"🔧 Calling {tool_name}...")
                response = await client.call_tool(tool_name, args)
                if response.success:
                    content = response.data.get("content", [])
                    for item in content:
                        print(item.get("text", str(item)))
                else:
                    print(f"❌ Error: {response.error}")
            else:
                print("❓ Unknown command. Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Client")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--test", "-t", action="store_true", help="Run tests")

    args = parser.parse_args()

    # Check server readiness first
    print("🔍 Checking server readiness...")
    import subprocess
    result = subprocess.run([sys.executable, "server_manager.py", "status"],
                          capture_output=True, text=True)

    if "Server environment ready" not in result.stdout:
        print("❌ Server environment not ready")
        print("💡 Run: python3 server_manager.py status")
        sys.exit(1)

    client = MCPClient()

    try:
        # Connect to server
        if not await client.connect():
            sys.exit(1)

        if args.interactive:
            await interactive_mode(client)
        elif args.test:
            success = await run_tests(client)
            sys.exit(0 if success else 1)
        else:
            # Default: run tests
            success = await run_tests(client)
            sys.exit(0 if success else 1)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Client interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

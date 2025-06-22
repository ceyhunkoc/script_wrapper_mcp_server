#!/usr/bin/env python3
"""
Simple MCP Server Manager

Manages server lifecycle but allows individual test clients to connect independently.
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


class ServerManager:
    """Simple server lifecycle management."""
    
    def __init__(self):
        self.pid_file = Path.cwd() / ".mcp_server_manager.pid"
        
    def is_server_ready(self) -> bool:
        """Check if the server environment is ready."""
        # Check if config file exists
        config_file = Path.cwd() / ".mcp-config.json"
        if not config_file.exists():
            print("❌ Configuration file not found: .mcp-config.json")
            return False
        
        # Check if source directory exists
        src_dir = Path.cwd() / "src" / "mcp_script_runner"
        if not src_dir.exists():
            print("❌ Source directory not found: src/mcp_script_runner")
            return False
        
        # Check if scripts directory exists
        scripts_dir = Path.cwd() / "scripts"
        if not scripts_dir.exists():
            print("❌ Scripts directory not found: scripts")
            return False
        
        return True
    
    def get_server_command(self) -> list:
        """Get the command to start the MCP server."""
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{Path.cwd() / 'src'}:{env.get('PYTHONPATH', '')}"
        
        return {
            "cmd": [sys.executable, "-m", "mcp_script_runner.server"],
            "env": env
        }
    
    def test_server_startup(self) -> bool:
        """Test if the server can start successfully."""
        if not self.is_server_ready():
            return False
        
        print("🧪 Testing server startup...")
        
        try:
            server_info = self.get_server_command()
            
            # Start server process
            process = subprocess.Popen(
                server_info["cmd"],
                env=server_info["env"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give it a moment to start
            time.sleep(1)
            
            # Send a simple initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "test", "version": "1.0.0"}
                }
            }
            
            request_json = json.dumps(init_request) + "\n"
            process.stdin.write(request_json.encode())
            process.stdin.flush()
            
            # Try to read response with timeout
            try:
                # Use select or timeout mechanism
                import select
                ready, _, _ = select.select([process.stdout], [], [], 3)
                
                if ready:
                    response_line = process.stdout.readline()
                    if response_line:
                        response = json.loads(response_line.decode().strip())
                        if "result" in response:
                            print("✅ Server startup test successful")
                            process.terminate()
                            process.wait()
                            return True
                
            except Exception as e:
                print(f"⚠️ Response parsing error: {e}")
            
            # Cleanup
            process.terminate()
            process.wait()
            print("❌ Server startup test failed")
            return False
            
        except Exception as e:
            print(f"❌ Server startup test failed: {e}")
            return False
    
    def status(self):
        """Show server status and configuration."""
        print("🔍 MCP Server Manager Status")
        print("=" * 40)
        
        # Check configuration
        if self.is_server_ready():
            print("✅ Server environment ready")
            
            # Show configuration details
            config_file = Path.cwd() / ".mcp-config.json"
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                    scripts = config.get("scripts", {})
                    print(f"   📜 Scripts configured: {len(scripts)}")
                    for name in scripts.keys():
                        print(f"      - {name}")
            except Exception as e:
                print(f"   ⚠️ Configuration error: {e}")
            
            # Test startup
            if self.test_server_startup():
                print("\n✅ Server is ready for client connections")
                print("💡 Use: python3 client.py to connect")
            else:
                print("\n❌ Server has startup issues")
        else:
            print("❌ Server environment not ready")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Server Manager")
    parser.add_argument("action", choices=["status", "test"], 
                       help="Action to perform")
    
    args = parser.parse_args()
    
    manager = ServerManager()
    
    if args.action == "status":
        manager.status()
    elif args.action == "test":
        success = manager.test_server_startup()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

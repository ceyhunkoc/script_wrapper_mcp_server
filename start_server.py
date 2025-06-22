#!/usr/bin/env python3
"""
MCP Script Runner Server Launcher

Starts the MCP server in the background and provides management commands.
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


class MCPServerManager:
    """Manages the MCP server process."""
    
    def __init__(self):
        self.pid_file = Path.cwd() / ".mcp_server.pid"
        self.log_file = Path.cwd() / "mcp_server.log"
        
    def _setup_environment(self) -> dict:
        """Setup environment variables for the server."""
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{Path.cwd() / 'src'}:{env.get('PYTHONPATH', '')}"
        return env
    
    def start_server(self, background: bool = True) -> bool:
        """Start the MCP server."""
        if self.is_running():
            print("✅ MCP server is already running")
            print(f"   PID: {self.get_pid()}")
            return True
        
        try:
            cmd = [sys.executable, "-m", "mcp_script_runner.server"]
            env = self._setup_environment()
            
            print(f"🚀 Starting MCP server: {' '.join(cmd)}")
            
            if background:
                # Start in background
                with open(self.log_file, "w") as log:
                    process = subprocess.Popen(
                        cmd,
                        env=env,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        stdin=subprocess.PIPE
                    )
                
                # Save PID
                with open(self.pid_file, "w") as f:
                    f.write(str(process.pid))
                
                # Give it time to start
                time.sleep(2)
                
                # Check if it's still running
                if process.poll() is None:
                    print(f"✅ MCP server started successfully")
                    print(f"   PID: {process.pid}")
                    print(f"   Log: {self.log_file}")
                    return True
                else:
                    print("❌ Server failed to start")
                    self._show_logs()
                    return False
            else:
                # Start in foreground
                print("🔧 Starting server in foreground mode...")
                print("   Press Ctrl+C to stop")
                try:
                    subprocess.run(cmd, env=env)
                except KeyboardInterrupt:
                    print("\n🛑 Server stopped")
                return True
                
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def stop_server(self) -> bool:
        """Stop the MCP server."""
        if not self.is_running():
            print("⚠️ MCP server is not running")
            return True
        
        try:
            pid = self.get_pid()
            if pid:
                print(f"🛑 Stopping MCP server (PID: {pid})")
                os.kill(pid, signal.SIGTERM)
                
                # Wait for graceful shutdown
                for _ in range(10):
                    if not self.is_running():
                        break
                    time.sleep(0.5)
                
                # Force kill if still running
                if self.is_running():
                    print("⚡ Force killing server...")
                    os.kill(pid, signal.SIGKILL)
                
                self._cleanup()
                print("✅ MCP server stopped")
                return True
                
        except ProcessLookupError:
            print("⚠️ Server process not found, cleaning up...")
            self._cleanup()
            return True
        except Exception as e:
            print(f"❌ Failed to stop server: {e}")
            return False
    
    def is_running(self) -> bool:
        """Check if the MCP server is running."""
        pid = self.get_pid()
        if not pid:
            return False
        
        try:
            os.kill(pid, 0)  # Signal 0 just checks if process exists
            return True
        except ProcessLookupError:
            self._cleanup()
            return False
    
    def get_pid(self) -> Optional[int]:
        """Get the PID of the running server."""
        if not self.pid_file.exists():
            return None
        
        try:
            with open(self.pid_file, "r") as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return None
    
    def status(self):
        """Show server status."""
        if self.is_running():
            pid = self.get_pid()
            print(f"✅ MCP server is running")
            print(f"   PID: {pid}")
            print(f"   Log: {self.log_file}")
            if self.log_file.exists():
                print(f"   Log size: {self.log_file.stat().st_size} bytes")
        else:
            print("❌ MCP server is not running")
    
    def show_logs(self):
        """Show server logs."""
        self._show_logs()
    
    def _show_logs(self):
        """Show the last few lines of server logs."""
        if self.log_file.exists():
            print(f"\n📋 Server logs ({self.log_file}):")
            print("-" * 50)
            try:
                with open(self.log_file, "r") as f:
                    lines = f.readlines()
                    # Show last 20 lines
                    for line in lines[-20:]:
                        print(line.rstrip())
            except Exception as e:
                print(f"❌ Could not read logs: {e}")
            print("-" * 50)
        else:
            print("⚠️ No log file found")
    
    def _cleanup(self):
        """Clean up PID file."""
        if self.pid_file.exists():
            self.pid_file.unlink()
    
    def restart_server(self) -> bool:
        """Restart the MCP server."""
        print("🔄 Restarting MCP server...")
        self.stop_server()
        time.sleep(1)
        return self.start_server()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Server Manager")
    parser.add_argument("action", choices=["start", "stop", "restart", "status", "logs"], 
                       help="Action to perform")
    parser.add_argument("--foreground", "-f", action="store_true", 
                       help="Start server in foreground (not background)")
    
    args = parser.parse_args()
    
    manager = MCPServerManager()
    
    if args.action == "start":
        success = manager.start_server(background=not args.foreground)
        sys.exit(0 if success else 1)
    elif args.action == "stop":
        success = manager.stop_server()
        sys.exit(0 if success else 1)
    elif args.action == "restart":
        success = manager.restart_server()
        sys.exit(0 if success else 1)
    elif args.action == "status":
        manager.status()
    elif args.action == "logs":
        manager.show_logs()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

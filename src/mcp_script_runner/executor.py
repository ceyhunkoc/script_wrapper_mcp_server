"""Script execution engine for MCP Script Runner."""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import ConfigManager, ScriptConfig


class ScriptExecutionResult:
    """Result of script execution."""

    def __init__(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        execution_time: float,
        script_name: str
    ):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.execution_time = execution_time
        self.script_name = script_name

    @property
    def success(self) -> bool:
        """Check if script executed successfully."""
        return self.exit_code == 0

    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            "script_name": self.script_name,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "execution_time": self.execution_time,
            "success": self.success
        }


class ScriptExecutor:
    """Executes bash scripts according to configuration."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    async def execute_script(
        self,
        script_name: str,
        arguments: Optional[List[str]] = None
    ) -> ScriptExecutionResult:
        """Execute a configured script by name.

        Args:
            script_name: Name of the script to execute
            arguments: Optional list of arguments to pass to script

        Returns:
            ScriptExecutionResult with execution details

        Raises:
            ValueError: If script is not found or invalid
        """
        script_config = self.config_manager.get_script_config(script_name)
        if not script_config:
            raise ValueError(f"Script not found: {script_name}")

        return await self._execute_script_config(script_config, arguments or [])

    async def _execute_script_config(
        self,
        script_config: ScriptConfig,
        arguments: List[str]
    ) -> ScriptExecutionResult:
        """Execute a script based on its configuration.

        Args:
            script_config: Configuration for the script
            arguments: Arguments to pass to script

        Returns:
            ScriptExecutionResult with execution details
        """
        import time
        start_time = time.time()

        # Prepare command
        cmd = ["bash", script_config.path] + arguments

        # Determine working directory
        working_dir = script_config.working_directory or self.config_manager.config.working_directory
        working_dir_path = Path(working_dir).resolve()

        process = None
        try:
            # Execute script with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(working_dir_path)
            )

            # Wait for completion with timeout
            stdout_data, stderr_data = await asyncio.wait_for(
                process.communicate(),
                timeout=script_config.timeout
            )

            execution_time = time.time() - start_time

            return ScriptExecutionResult(
                exit_code=process.returncode or 0,
                stdout=stdout_data.decode('utf-8'),
                stderr=stderr_data.decode('utf-8'),
                execution_time=execution_time,
                script_name=script_config.name
            )

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            # Kill the process if it's still running
            if process and process.returncode is None:
                process.kill()
                await process.wait()

            return ScriptExecutionResult(
                exit_code=124,  # Standard timeout exit code
                stdout="",
                stderr=f"Script execution timed out after {script_config.timeout} seconds",
                execution_time=execution_time,
                script_name=script_config.name
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return ScriptExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"Error executing script: {str(e)}",
                execution_time=execution_time,
                script_name=script_config.name
            )

    def list_available_scripts(self) -> List[Dict]:
        """List all available scripts with their metadata.

        Returns:
            List of dictionaries containing script information
        """
        scripts = []
        for script_name in self.config_manager.list_scripts():
            script_config = self.config_manager.get_script_config(script_name)
            if script_config:
                scripts.append({
                    "name": script_config.name,
                    "description": script_config.description,
                    "path": script_config.path,
                    "arguments": script_config.arguments,
                    "timeout": script_config.timeout
                })
        return scripts

    def get_script_info(self, script_name: str) -> Optional[Dict]:
        """Get detailed information about a specific script.

        Args:
            script_name: Name of the script

        Returns:
            Dictionary with script information or None if not found
        """
        script_config = self.config_manager.get_script_config(script_name)
        if not script_config:
            return None

        return {
            "name": script_config.name,
            "description": script_config.description,
            "path": script_config.path,
            "arguments": script_config.arguments,
            "timeout": script_config.timeout,
            "working_directory": script_config.working_directory
        }
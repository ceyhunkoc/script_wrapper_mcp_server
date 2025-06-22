"""Configuration management for MCP Script Runner."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class ScriptConfig(BaseModel):
    """Configuration for a single script."""

    name: str = Field(..., description="Name of the script")
    path: str = Field(..., description="Path to the script file")
    description: str = Field("", description="Description of what the script does")
    arguments: List[str] = Field(default_factory=list, description="List of argument names")
    working_directory: Optional[str] = Field(None, description="Working directory for script execution")
    timeout: int = Field(300, description="Script execution timeout in seconds")

    @validator('path')
    def validate_path(cls, v: str) -> str:
        """Validate that the script path exists."""
        if not os.path.exists(v):
            raise ValueError(f"Script path does not exist: {v}")
        return v


class MCPConfig(BaseModel):
    """Main configuration for MCP Script Runner."""

    working_directory: str = Field(default=".", description="Default working directory")
    scripts: Dict[str, ScriptConfig] = Field(default_factory=dict, description="Script configurations")
    docker_image: str = Field("ubuntu:22.04", description="Docker image to use for execution")
    container_name: str = Field("mcp-script-runner", description="Docker container name")
    mount_path: str = Field("/workspace", description="Path to mount project files in container")

    @validator('working_directory')
    def validate_working_directory(cls, v: str) -> str:
        """Validate that the working directory exists."""
        if not os.path.exists(v):
            raise ValueError(f"Working directory does not exist: {v}")
        return v


class ConfigManager:
    """Manages loading and validation of MCP configuration."""

    def __init__(self, config_path: str = ".mcp-config.json"):
        self.config_path = Path(config_path)
        self._config: Optional[MCPConfig] = None

    def load_config(self) -> MCPConfig:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                self._config = MCPConfig(**config_data)
            except Exception as e:
                raise ValueError(f"Failed to load configuration: {e}")
        else:
            # Create default configuration
            self._config = MCPConfig(
                working_directory=".",
                docker_image="ubuntu:22.04",
                container_name="mcp-script-runner",
                mount_path="/workspace"
            )
            self._save_default_config()

        return self._config

    def _save_default_config(self) -> None:
        """Save default configuration to file."""
        default_config = {
            "working_directory": ".",
            "scripts": {
                "hello": {
                    "name": "hello",
                    "path": "./scripts/hello.sh",
                    "description": "Simple hello world script",
                    "arguments": [],
                    "timeout": 30
                }
            },
            "docker_image": "ubuntu:22.04",
            "container_name": "mcp-script-runner",
            "mount_path": "/workspace"
        }

        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)

    def reload_config(self) -> MCPConfig:
        """Reload configuration from file."""
        self._config = None
        return self.load_config()

    @property
    def config(self) -> MCPConfig:
        """Get current configuration, loading if necessary."""
        if self._config is None:
            return self.load_config()
        return self._config

    def get_script_config(self, script_name: str) -> Optional[ScriptConfig]:
        """Get configuration for a specific script."""
        return self.config.scripts.get(script_name)

    def list_scripts(self) -> List[str]:
        """List all available script names."""
        return list(self.config.scripts.keys())
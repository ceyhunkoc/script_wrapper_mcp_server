"""Tests for configuration management."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_script_runner.config import ConfigManager, MCPConfig, ScriptConfig


class TestScriptConfig:
    """Test ScriptConfig validation."""

    def test_valid_script_config(self, tmp_path):
        """Test creating a valid script configuration."""
        # Create a test script file
        script_path = tmp_path / "test_script.sh"
        script_path.write_text("#!/bin/bash\necho 'test'")

        config = ScriptConfig(
            name="test",
            path=str(script_path),
            description="Test script",
            arguments=["arg1", "arg2"],
            timeout=60
        )

        assert config.name == "test"
        assert config.path == str(script_path)
        assert config.description == "Test script"
        assert config.arguments == ["arg1", "arg2"]
        assert config.timeout == 60

    def test_nonexistent_script_path(self):
        """Test that nonexistent script path raises ValueError."""
        with pytest.raises(ValueError, match="Script path does not exist"):
            ScriptConfig(
                name="test",
                path="/nonexistent/path.sh",
                description="Test script"
            )


class TestMCPConfig:
    """Test MCPConfig validation."""

    def test_valid_config(self, tmp_path):
        """Test creating a valid MCP configuration."""
        config = MCPConfig(
            working_directory=str(tmp_path),
            docker_image="ubuntu:22.04",
            container_name="test-container",
            mount_path="/workspace"
        )

        assert config.working_directory == str(tmp_path)
        assert config.docker_image == "ubuntu:22.04"
        assert config.container_name == "test-container"
        assert config.mount_path == "/workspace"

    def test_nonexistent_working_directory(self):
        """Test that nonexistent working directory raises ValueError."""
        with pytest.raises(ValueError, match="Working directory does not exist"):
            MCPConfig(
                working_directory="/nonexistent/path",
                docker_image="ubuntu:22.04",
                container_name="test-container",
                mount_path="/workspace"
            )


class TestConfigManager:
    """Test ConfigManager functionality."""

    def test_load_config_creates_default(self, tmp_path):
        """Test that loading config creates default when file doesn't exist."""
        config_path = tmp_path / ".mcp-config.json"

        with patch('os.path.exists', return_value=True):
            manager = ConfigManager(str(config_path))
            config = manager.load_config()

        assert isinstance(config, MCPConfig)
        assert config.working_directory == "."
        assert config.docker_image == "ubuntu:22.04"

    def test_load_existing_config(self, tmp_path):
        """Test loading an existing configuration file."""
        config_path = tmp_path / ".mcp-config.json"
        script_path = tmp_path / "test.sh"
        script_path.write_text("#!/bin/bash\necho 'test'")

        config_data = {
            "working_directory": str(tmp_path),
            "scripts": {
                "test": {
                    "name": "test",
                    "path": str(script_path),
                    "description": "Test script",
                    "arguments": [],
                    "timeout": 30
                }
            },
            "docker_image": "ubuntu:22.04",
            "container_name": "test-container",
            "mount_path": "/workspace"
        }

        with open(config_path, 'w') as f:
            json.dump(config_data, f)

        manager = ConfigManager(str(config_path))
        config = manager.load_config()

        assert config.working_directory == str(tmp_path)
        assert "test" in config.scripts
        assert config.scripts["test"].name == "test"

    def test_get_script_config(self, tmp_path):
        """Test getting script configuration by name."""
        config_path = tmp_path / ".mcp-config.json"
        script_path = tmp_path / "test.sh"
        script_path.write_text("#!/bin/bash\necho 'test'")

        config_data = {
            "working_directory": str(tmp_path),
            "scripts": {
                "test": {
                    "name": "test",
                    "path": str(script_path),
                    "description": "Test script",
                    "arguments": [],
                    "timeout": 30
                }
            },
            "docker_image": "ubuntu:22.04",
            "container_name": "test-container",
            "mount_path": "/workspace"
        }

        with open(config_path, 'w') as f:
            json.dump(config_data, f)

        manager = ConfigManager(str(config_path))
        manager.load_config()

        script_config = manager.get_script_config("test")
        assert script_config is not None
        assert script_config.name == "test"

        # Test nonexistent script
        assert manager.get_script_config("nonexistent") is None

    def test_list_scripts(self, tmp_path):
        """Test listing available scripts."""
        config_path = tmp_path / ".mcp-config.json"
        script_path = tmp_path / "test.sh"
        script_path.write_text("#!/bin/bash\necho 'test'")

        config_data = {
            "working_directory": str(tmp_path),
            "scripts": {
                "test1": {
                    "name": "test1",
                    "path": str(script_path),
                    "description": "Test script 1",
                    "arguments": [],
                    "timeout": 30
                },
                "test2": {
                    "name": "test2",
                    "path": str(script_path),
                    "description": "Test script 2",
                    "arguments": [],
                    "timeout": 30
                }
            },
            "docker_image": "ubuntu:22.04",
            "container_name": "test-container",
            "mount_path": "/workspace"
        }

        with open(config_path, 'w') as f:
            json.dump(config_data, f)

        manager = ConfigManager(str(config_path))
        manager.load_config()

        scripts = manager.list_scripts()
        assert len(scripts) == 2
        assert "test1" in scripts
        assert "test2" in scripts
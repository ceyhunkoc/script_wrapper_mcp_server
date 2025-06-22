#! /bin/bash
script_dir=$(dirname "$0")
export PYTHONPATH=$script_dir/src
python3 -m mcp_script_runner.server
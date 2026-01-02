#!/bin/bash
set -e

# Move into the MCP server directory
cd /home/djr/ai-server/mcp-server

# Activate the virtual environment
source venv/bin/activate

# Launch MCP server using the venv's uvicorn
exec /home/djr/ai-server/mcp-server/venv/bin/uvicorn server:app --fd 3 --root-path /



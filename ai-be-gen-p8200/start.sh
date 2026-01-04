#!/bin/bash
set -e

# Move into the backend directory
cd /home/djr/ai-server/ai-be-gen-p8200

# Activate the virtual environment
source venv/bin/activate

# Launch the backend using the venv's uvicorn
exec /home/djr/ai-server/ai-be-gen-p8200/venv/bin/uvicorn ai-backend-server:app --host 0.0.0.0 --port 8200


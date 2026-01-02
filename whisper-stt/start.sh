#!/bin/bash
cd /home/djr/ai-server/whisper-stt
source venv/bin/activate
exec /home/djr/ai-server/whisper-stt/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8001

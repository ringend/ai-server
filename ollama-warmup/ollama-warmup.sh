#!/bin/bash

# Model to warm up (default: llama3)
MODEL="${1:-llama3.1:8b}"
MODEL2="${1:-phi4}"

# Ollama API endpoints
HEALTH_URL="http://localhost:11434/api/tags"
GENERATE_URL="http://localhost:11434/api/generate"
GENERATE_URL2="http://localhost:11435/api/generate"

# Wait until Ollama is responding
echo "Waiting for Ollama to start..."

for i in {1..30}; do
    if curl -s --max-time 1 "$HEALTH_URL" >/dev/null; then
        echo "Ollama is up."
        break
    fi
    sleep 5
done

# If still not up, exit gracefully
if ! curl -s --max-time 1 "$HEALTH_URL" >/dev/null; then
    echo "Ollama did not start in time. Exiting."
    exit 1
fi

# Warm up the model
echo "Warming up model: $MODEL"

curl --max-time 30 \
     -X POST "$GENERATE_URL" \
     -d "{\"model\":\"$MODEL\",\"prompt\":\"hello\"}" \
     >/dev/null 2>&1

echo "Warm-up complete."

# Warm up model #2
echo "Warming up model: $MODEL2"

curl --max-time 30 \
     -X POST "$GENERATE_URL2" \
     -d "{\"model\":\"$MODEL2\",\"prompt\":\"hello\"}" \
     >/dev/null 2>&1

echo "Warm-up complete."

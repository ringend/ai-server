#!/bin/bash

# === CONFIGURATION ===
MODEL="llama3.1:8b"
TOKENS=300
CONTEXT=4096
TEMPERATURE=0.0
PROMPT="Summarize Romans 8 in 3 sentences."

# === FUNCTIONS ===

function stop_ollama_service() {
  echo "🛑 Stopping Ollama service..."
  sudo systemctl stop ollama
  sleep 2
}

function start_ollama_service() {
  echo "🚀 Restarting Ollama service..."
  sudo systemctl start ollama
}

function run_benchmark() {
  echo "📊 Running benchmark for model: $MODEL"
  ollama benchmark "$MODEL" \
    --tokens "$TOKENS" \
    --context "$CONTEXT" \
    --temperature "$TEMPERATURE" \
    --prompt "$PROMPT"
}

function main() {
  stop_ollama_service
  run_benchmark
  start_ollama_service
}

main

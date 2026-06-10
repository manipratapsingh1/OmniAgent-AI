#!/usr/bin/env bash
set -euo pipefail
echo "⏬ Pulling default Ollama models (this can take a while)…"
docker exec -it $(docker ps -qf "ancestor=ollama/ollama:latest") ollama pull llama3.2
docker exec -it $(docker ps -qf "ancestor=ollama/ollama:latest") ollama pull nomic-embed-text
echo "✅ Models ready."
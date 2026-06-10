#!/usr/bin/env bash
set -euo pipefail
cp -n .env.example .env || true
echo "✅ .env ready. Now run: make up && make models"
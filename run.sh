#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

export PYTHONPATH="$PROJECT_ROOT"

uvicorn bookService.service.app.main:app \
  --reload \
  --host 127.0.0.1 \
  --port 8000

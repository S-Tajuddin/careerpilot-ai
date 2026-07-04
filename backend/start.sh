#!/bin/bash
# =============================================================
# CareerPilot AI — Start Backend (Linux/Mac)
# Run from: careerpilot-ai/backend/
# =============================================================

set -e

echo ""
echo "============================================"
echo "  CareerPilot AI - Starting Backend"
echo "============================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found!"
    exit 1
fi

# Check .env
if [ ! -f ".env" ]; then
    echo "[ERROR] .env file not found!"
    echo "Copy .env.example to .env and fill in your API keys."
    exit 1
fi

# Create venv if needed
if [ ! -d ".venv" ]; then
    echo "[SETUP] Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install deps
echo "[SETUP] Installing dependencies..."
pip install -q -r requirements.txt

# Ensure data dirs
mkdir -p data/chroma data/resumes data/cover_letters data/exports

# Check Ollama
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "[OK] Ollama is running!"
else
    echo "[WARNING] Ollama is NOT running! Start it: ollama serve"
    echo "  Backend will start, but AI features won't work."
fi

# Start server
echo ""
echo "[START] Launching CareerPilot AI backend..."
echo "  API:     http://localhost:8000"
echo "  Docs:    http://localhost:8000/docs"
echo "  Health:  http://localhost:8000/health"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

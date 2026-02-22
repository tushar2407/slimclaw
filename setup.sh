#!/bin/bash
set -e

if [ -d "venv" ]; then
  echo "==> venv already exists, skipping install..."
else
  echo "==> Creating virtualenv and installing dependencies..."
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
fi

echo "==> Checking Ollama..."
if ! command -v ollama &> /dev/null; then
  echo "Ollama not found. Installing via Homebrew..."
  if ! command -v brew &> /dev/null; then
    echo "ERROR: Homebrew not found. Install it first: https://brew.sh"
    exit 1
  fi
  brew install ollama
fi

echo "==> Starting Ollama service..."
brew services start ollama

echo "==> Pulling qwen2.5:7b model (this may take a while)..."
ollama pull qwen2.5:7b

echo "==> Setting up ~/.slimclaw/..."
mkdir -p ~/.slimclaw
if [ ! -f ~/.slimclaw/SOUL.md ]; then
  cp workspace/SOUL.md ~/.slimclaw/SOUL.md
  echo "Created ~/.slimclaw/SOUL.md"
fi
if [ ! -f ~/.slimclaw/MEMORY.md ]; then
  touch ~/.slimclaw/MEMORY.md
  echo "Created ~/.slimclaw/MEMORY.md"
fi

echo ""
echo "Setup complete. Run with: source venv/bin/activate && python main.py"

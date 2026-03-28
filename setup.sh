#!/bin/bash
set -e

if [ -d ".venv" ]; then
  echo "==> .venv already exists, skipping venv creation..."
else
  echo "==> Creating virtualenv with uv..."
  uv venv
fi

echo "==> Installing dependencies..."
uv pip install -e ".[dev]"

echo "==> Setting up pre-commit hooks..."
uv run pre-commit install

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

echo "==> Pulling nomic-embed-text model for semantic search..."
ollama pull nomic-embed-text

echo "==> Setting up ~/.slimclaw/..."
mkdir -p ~/.slimclaw
mkdir -p ~/.slimclaw/sessions
mkdir -p ~/.slimclaw/memory

if [ ! -f ~/.slimclaw/SOUL.md ]; then
  cp workspace/SOUL.md ~/.slimclaw/SOUL.md
  echo "Created ~/.slimclaw/SOUL.md"
fi
if [ ! -f ~/.slimclaw/MEMORY.md ]; then
  touch ~/.slimclaw/MEMORY.md
  echo "Created ~/.slimclaw/MEMORY.md"
fi

echo "==> Initializing database..."
sqlite3 ~/.slimclaw/slimclaw.db <<'EOF'
-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_key TEXT NOT NULL UNIQUE,
    agent_id TEXT NOT NULL DEFAULT 'default',
    channel TEXT NOT NULL,
    scope TEXT NOT NULL,
    identifier TEXT NOT NULL,
    thread_id TEXT,
    started_at TEXT NOT NULL,
    last_active_at TEXT NOT NULL,
    metadata TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_channel ON sessions(channel);
CREATE INDEX IF NOT EXISTS idx_sessions_last_active ON sessions(last_active_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent_id);

-- Embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_key TEXT NOT NULL,
    message_index INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    embedding BLOB NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(session_key, message_index)
);
CREATE INDEX IF NOT EXISTS idx_embeddings_session ON embeddings(session_key);
CREATE INDEX IF NOT EXISTS idx_embeddings_hash ON embeddings(content_hash);

-- Consolidation state table
CREATE TABLE IF NOT EXISTS consolidation_state (
    session_key TEXT PRIMARY KEY,
    last_processed_index INTEGER DEFAULT 0,
    last_consolidated_at TEXT
);
EOF
echo "Database initialized at ~/.slimclaw/slimclaw.db"

echo ""
echo "Setup complete. Run with: source .venv/bin/activate && python main.py"

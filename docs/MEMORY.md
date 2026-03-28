# Memory System

SlimClaw's memory system provides persistent storage and retrieval of conversation history with semantic search capabilities.

## Directory Structure

```
~/.slimclaw/
├── slimclaw.db          # SQLite database (sessions, embeddings, consolidation state)
├── MEMORY.md            # User notes (written via memory_write tool)
├── sessions/            # JSONL message 
│   └── agent_default_cli_user_tush.jsonl
└── memory/              # Consolidated memory files (daily)
    └── 2024-03-07.md
```

## Components

### 1. Message Archive (`memory/archive.py`)

Stores raw conversation history as JSONL files.

```python
from slimclaw.memory import MessageArchive

archive = MessageArchive()
archive.archive_message(
    session_key="agent:default:cli:user:tush",
    role="human",
    content="Hello!"
)
```

Each message is stored as a JSON line:
```json
{"role": "human", "content": "Hello!", "ts": "2024-03-07T10:30:00", "tool_name": null, "tool_args": null}
```

### 2. Embeddings (`memory/embeddings/`)

Vector embeddings for semantic search using Ollama or OpenAI.

```python
from slimclaw.memory import EmbeddingStore, get_embedding, EmbeddingProvider

# Generate embedding
embedding = get_embedding("search query", provider=EmbeddingProvider.OLLAMA)

# Store and search
store = EmbeddingStore()
store.add_embedding(session_key, message_index, content, embedding)
results = store.search(query_embedding, top_k=10)
```

**Files:**
- `types.py` - `EmbeddingProvider` enum, `SearchResult` dataclass
- `providers.py` - `get_embedding()` for Ollama/OpenAI
- `store.py` - `EmbeddingStore` class (SQLite storage)
- `utils.py` - `cosine_similarity()`

### 3. Memory Consolidation (`memory/consolidator.py`)

Extracts facts, summaries, and action items from conversations using LLM.

```python
from slimclaw.memory import MemoryConsolidator

consolidator = MemoryConsolidator(llm, consolidation_threshold=10)

if consolidator.should_consolidate(session_key):
    consolidator.consolidate(session_key)
```

Output is written to daily files in `~/.slimclaw/memory/`:
```markdown
# Memory Log - 2024-03-07

## Session: agent:default:cli:user:tush (10:30)

### Facts
- User prefers dark mode
- Project uses Python 3.11

### Summary
Discussed UI preferences and project setup.

### Action Items
- [ ] Add dark mode toggle
```

### 4. Search (`memory/search.py`)

Two search modes: regex and semantic.

**Regex Search:**
```python
from slimclaw.memory import memory_search

# Searches MEMORY.md, memory/*.md, and sessions/*.jsonl
results = memory_search("python", case_insensitive=True)
```

**Semantic Search:**
```python
results = memory_search("how to set up the project", semantic=True, top_k=10)
```

**Read Memory:**
```python
from slimclaw.memory import memory_get

content = memory_get("MEMORY.md")
content = memory_get("memory/2024-03-07.md", line_range="1-50")
```

**Write Notes:**
```python
from slimclaw.memory import memory_write

memory_write("User prefers vim keybindings")
# Appends: "- [2024-03-07 10:30] User prefers vim keybindings" to MEMORY.md
```

## Database Tables

### sessions
Session metadata (managed by `sessions/` module).

### embeddings
Vector embeddings for semantic search.

| Column | Type | Description |
|--------|------|-------------|
| session_key | TEXT | Session identifier |
| message_index | INTEGER | Message position in JSONL |
| content_hash | TEXT | SHA256 hash (first 16 chars) |
| embedding | BLOB | Float32 vector bytes |

### consolidation_state
Tracks consolidation progress per session.

| Column | Type | Description |
|--------|------|-------------|
| session_key | TEXT | Session identifier |
| last_processed_index | INTEGER | Last consolidated message index |
| last_consolidated_at | TEXT | ISO timestamp |

## Configuration

In `~/.slimclaw/config.json`:

```json
{
  "embeddings": {
    "provider": "ollama",
    "model": "nomic-embed-text",
    "enabled": true,
    "consolidation_threshold": 10
  }
}
```

## Tools

The agent has access to three memory tools:

1. **memory_write** - Save notes to MEMORY.md
2. **memory_search** - Search memory files and session history
3. **memory_get** - Read from memory files

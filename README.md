# slimclaw

A lightweight, local-first CLI personal assistant powered by Ollama.

## What is slimclaw?

slimclaw is a terminal-based AI assistant that runs entirely on your machine. No cloud APIs required — just you and a local LLM.

## Quick Start

**Prerequisites:** Python 3.11+, [Ollama](https://ollama.ai)

```bash
git clone https://github.com/tushar2407/slimclaw.git
cd slimclaw
chmod +x setup.sh
./setup.sh
```

`setup.sh` creates a virtual environment, installs dependencies, installs Ollama if needed, pulls the default model (`qwen2.5:7b`), and sets up `~/.slimclaw/`.

```bash
source .venv/bin/activate
python main.py
```

## Tools

| Tool | Description |
|------|-------------|
| `read` | Read a file |
| `write` | Create or overwrite a file |
| `edit` | String replacement in files (supports glob patterns) |
| `shell` | Run shell commands (requires confirmation) |
| `grep` | Regex search with context lines |
| `find` | Glob pattern file search |
| `ls` | Directory listing |
| `web_search` | Search the web via DuckDuckGo |
| `memory_write` | Save a note to persistent memory |
| `memory_search` | Search memory and session history |
| `memory_get` | Read specific sections of memory files |
| `schedule_reminder` | Schedule a one-time desktop notification |
| `list_reminders` | List scheduled reminders |
| `cancel_reminder` | Cancel a reminder by ID |
| `spawn_agent` | Delegate a task to a specialised subagent |

## Subagents

The agent can spawn child agents to handle specialised subtasks. Agent types are defined in `~/.slimclaw/AGENTS.md`:

```markdown
## researcher
description: Web search and summarisation only.
tools: web_search, memory_write, memory_search
model: inherit

## coder
description: Reads, writes, and runs code.
tools: read, write, edit, shell, grep, find, ls
model: inherit
```

Child agents run in a background thread and return their result to the parent. Nesting is limited to depth 2.

## Configuration

Model and provider are set interactively with `/model` at the prompt, or by editing `~/.slimclaw/config.json`:

```json
{
  "llm": {
    "provider": "ollama",
    "model": "qwen2.5:7b",
    "base_url": "http://localhost:11434"
  },
  "shell": {
    "auto_run": null
  }
}
```

`shell.auto_run`: `null` = ask each time, `true` = always allow, `false` = always deny.

Supported providers: `ollama`, `openai`, `anthropic`.

## Customisation

| File | Purpose |
|------|---------|
| `~/.slimclaw/SOUL.md` | Agent personality and behaviour |
| `~/.slimclaw/MEMORY.md` | Persistent memory across sessions |
| `~/.slimclaw/AGENTS.md` | Subagent type definitions |

## Slash Commands

| Command | Action |
|---------|--------|
| `/model` | Switch provider and model |
| `/new` | Reset conversation |
| `/exit` | Quit |

## Project Structure

```
src/slimclaw/
├── agent/       # SlimclawAgent (LangGraph), subagent runner and types
├── cli/         # REPL loop, Rich UI, session management
├── config/      # Config loading, constants, paths
├── cron/        # Background scheduler, job persistence, notifications
├── llm/         # Provider factory (Ollama, OpenAI, Anthropic)
├── memory/      # JSONL archive, embeddings, semantic search
├── prompt/      # Modular system prompt builder
├── sessions/    # SQLite session management
└── tools/       # All tool definitions

~/.slimclaw/
├── config.json  # Model and settings
├── SOUL.md      # Agent personality
├── MEMORY.md    # Persistent memory
├── AGENTS.md    # Subagent definitions
└── jobs.json    # Scheduled reminders
```

## Development

```bash
git clone https://github.com/tushar2407/slimclaw.git
cd slimclaw
./setup.sh

# Lint
ruff check .
ruff format .
```

### Adding a Tool

1. Create a function in `src/slimclaw/tools/` and decorate with `@tool` from `langchain_core.tools`
2. Add it to the `TOOLS` list in `src/slimclaw/tools/__init__.py`
3. Add a description entry in `src/slimclaw/prompt/sections/tooling.py`

## License

MIT

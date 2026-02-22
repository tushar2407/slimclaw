# slimclaw

A lightweight, local-first CLI personal assistant powered by Ollama.

## What is slimclaw?

slimclaw is a terminal-based AI assistant that runs entirely on your machine. No cloud APIs, no subscriptions — just you and a local LLM having a conversation.

**Core capabilities:**
- **Read/write files** in your working directory
- **Run shell commands** with your approval
- **Search the web** via DuckDuckGo
- **Persistent memory** across sessions

## Vision

slimclaw is Phase 1 of the [OpenClaw](https://github.com/tush/openclaw) ecosystem — a modular, extensible AI assistant platform.

**Phase 1 (slimclaw):** Local CLI assistant with core tools
**Phase 2 (OpenClaw):** Multi-channel (WhatsApp, Discord, Telegram), web UI, scheduled tasks, plugins

The goal is an assistant that's genuinely useful, runs locally, respects your privacy, and can grow with your needs.

## Quick Start

### Prerequisites

- Python 3.11+
- [Homebrew](https://brew.sh) (macOS)

### Setup

```bash
git clone https://github.com/tushar2407/slimclaw.git
cd slimclaw
chmod +x setup.sh
./setup.sh
```

This will:
1. Create a Python virtual environment
2. Install dependencies
3. Install Ollama (if needed)
4. Pull the default model (`qwen2.5:7b`)
5. Set up `~/.slimclaw/` for agent configuration

### Run

```bash
source venv/bin/activate
python main.py
```


### Tools

The agent has access to these tools:

| Tool | Description |
|------|-------------|
| `read` | Read files (relative to working directory) |
| `write` | Create/overwrite files |
| `shell` | Run shell commands (with confirmation) |
| `web_search` | Search the web via DuckDuckGo |
| `memory` | Save notes to persistent memory |

## Configuration

### Model

Edit `config.json` to change the model:

```json
{
  "model": "qwen2.5:7b",
  "ollama_base_url": "http://localhost:11434",
  "shell_auto_run": null
}
```

**Recommended models:**
- `qwen2.5:7b` — Good balance of speed and capability
- `llama3.2:3b` — Faster, lighter
- `qwen2.5:14b` — More capable, slower

### Personality

Edit `~/.slimclaw/SOUL.md` to customize the agent's personality and behavior.

### Memory

The agent stores persistent notes in `~/.slimclaw/MEMORY.md`. This survives across sessions and helps the agent remember context about you and your projects.

## Project Structure

```
slimclaw/
├── main.py          # CLI entrypoint
├── agent.py         # LLM orchestration + streaming
├── tools.py         # Tool definitions
├── config.json      # Model + settings
├── setup.sh         # Automated setup
├── requirements.txt # Dependencies
└── workspace/       # Template files (copied to ~/.slimclaw/ on setup)

~/.slimclaw/         # Agent configuration (created by setup.sh)
├── SOUL.md          # Agent personality
└── MEMORY.md        # Persistent memory
```

## Contributing

Contributions welcome! Here's how to get started:

### Development Setup

```bash
git clone https://github.com/tush/slimclaw.git
cd slimclaw
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Guidelines

1. **Keep it simple** — slimclaw is intentionally minimal
2. **Local-first** — avoid cloud dependencies
3. **Test your changes** — run the assistant and verify tools work
4. **Follow existing patterns** — look at how current tools are implemented

### Adding a New Tool

1. Add your function to `tools.py`
2. Add it to the `TOOLS` list with a `StructuredTool.from_function()` wrapper
3. Update the `## Tools` section in `agent.py:build_system_prompt()` if needed

### Pull Requests

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Test thoroughly
5. Submit a PR with a clear description

## License

MIT

## Acknowledgments

Built with:
- [Ollama](https://ollama.ai) — Local LLM inference
- [LangChain](https://langchain.com) — Agent orchestration
- [Rich](https://rich.readthedocs.io) — Beautiful terminal output

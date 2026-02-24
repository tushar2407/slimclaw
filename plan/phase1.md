# SlimClaw — Phase 1 (Complete)

Python CLI personal assistant. Local-first, Ollama-powered.

---

## Stack

- **Python 3.11+**
- **Ollama** — local LLM (qwen2.5:7b)
- **LangChain** — tool loop + agent orchestration
- **Rich** — pretty CLI output with streaming

---

## Project Structure

```
slimclaw/
├── main.py                 # CLI entrypoint
├── agent.py                # Agent orchestration
├── config.json             # Model + settings
├── requirements.txt
├── setup.sh
│
├── prompt/                 # Modular system prompt
│   ├── __init__.py
│   ├── builder.py          # Main prompt builder
│   ├── sections/
│   │   ├── __init__.py
│   │   ├── identity.py     # "You are..."
│   │   ├── environment.py  # cwd, datetime, platform
│   │   ├── tooling.py      # Tool descriptions
│   │   ├── behaviour.py    # Guidelines
│   │   ├── workspace.py    # Working directory info
│   │   └── persona.py      # SOUL.md, MEMORY.md
│   └── types.py            # PromptContext type
│
├── tools/                  # Tool modules
│   ├── __init__.py         # TOOLS list export
│   ├── read.py
│   ├── write.py
│   ├── shell.py
│   ├── web_search.py
│   └── memory.py
│
├── sessions/               # JSONL chat history
│
└── ~/.slimclaw/            # User data
    ├── SOUL.md             # Persona
    └── MEMORY.md           # Persistent memory
```

---

## Tools (7)

| Tool | Description |
|------|-------------|
| `read` | Read file contents |
| `write` | Write/create files |
| `shell` | Run shell commands (with confirmation flow) |
| `web_search` | Search the web via DuckDuckGo |
| `memory` | Append notes to MEMORY.md |
| `memory_search` | Search memory files and session history for a regex pattern |
| `memory_get` | Read from memory files (~/.slimclaw/) with optional line ranges |

---

## System Prompt Architecture

Modular builder pattern with 6 sections:

```python
def build_system_prompt(ctx: PromptContext) -> str:
    sections = [
        build_identity_section(),
        build_environment_section(ctx.env),
        build_tooling_section(ctx.tools),
        build_behaviour_section(),
        build_workspace_section(ctx.cwd),
        build_persona_section(ctx.soul, ctx.memory),
    ]
    return "\n".join(s for s in sections if s)
```

| Section | Content |
|---------|---------|
| Identity | "You are a personal assistant running inside slimclaw." |
| Environment | cwd, datetime, platform, user, git_branch |
| Tooling | Tool list with descriptions, usage guidance |
| Behaviour | Action over announcement, conciseness |
| Workspace | Working directory info |
| Persona | SOUL.md content, MEMORY.md content |

---

## Features

### CLI
- `python main.py` — starts interactive chat loop
- `/new` — reset session
- `/exit` — quit
- Rich streaming UI with spinner

### Shell Confirmation Flow
- Config-based: `auto_run` can be `true`, `false`, or `null` (ask each time)
- User can respond: `y`, `n`, `always`, `never`
- Preference persisted to config.json

### Session Persistence
- Each session saved to `sessions/<id>.jsonl`
- Turns appended on each exchange

---

## What's NOT in Phase 1

- No channels (WhatsApp, Telegram, etc.)
- No WebSockets
- No heartbeats / cron
- No subagents
- No plugins
- No web UI
- No vector memory / embeddings

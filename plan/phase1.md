# slimclaw — Phase 1 Plan

Python CLI personal assistant. Local-first, Ollama-powered, CopilotKit-ready.

---

## Stack

- **Python 3.11+**
- **Ollama** — local LLM (recommended: `llama3.2` or `qwen2.5` — both run well on M1 Pro)
- **CopilotKit SDK (Python)** — wraps the agent so it can later plug into any frontend
- **LangChain** — tool loop + agent orchestration
- **Rich** — pretty CLI output

---

## Project Structure

```v
slimclaw/
├── main.py               # CLI entrypoint
├── agent.py              # CopilotKit agent + tool loop
├── tools.py              # Built-in tools
├── workspace/
│   ├── SOUL.md           # Persona
│   └── MEMORY.md         # Persistent memory
├── sessions/             # JSONL chat history
├── config.json           # Model + settings
└── requirements.txt
```

---

## Phase 1 Scope

### CLI
- `python main.py` — starts interactive chat loop
- `/new` — reset session
- `/exit` — quit

### Agent
- System prompt built from `SOUL.md` + session history
- Tool loop: LLM calls tool → result appended → LLM continues until final reply
- Session saved to `sessions/<id>.jsonl` on each turn

### Built-in Tools (5 only)
| Tool | What it does |
|------|-------------|
| `read_file` | Read a file from workspace |
| `write_file` | Write/overwrite a file |
| `run_shell` | Run a shell command, return output |
| `web_search` | DuckDuckGo search (no API key needed) |
| `memory_write` | Append a note to MEMORY.md |

### CopilotKit Integration
- Agent wrapped as a `CopilotKitSDK` action
- This means zero rework when adding a web UI later

---

## What's explicitly NOT in Phase 1
- No channels (WhatsApp, Telegram, etc.)
- No WebSockets
- No heartbeats / cron
- No subagents
- No plugins
- No web UI

---

## Questions for review
1. `llama3.2` or `qwen2.5` as default model? (both fit M1 Pro 16GB)
2. Should `run_shell` require confirmation before executing, or just run?
3. Any tools you want swapped in/out from the list of 5?

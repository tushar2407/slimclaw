# SlimClaw Phase 2

## Overview
Expand slimclaw with more powerful tools and a modular system prompt architecture inspired by openclaw.

## New Tools

### File Tools
| Tool | Description |
|------|-------------|
| `edit` | Precise string replacement in files (old_string → new_string) |
| `grep` | Search file contents with regex patterns |
| `find` | Find files by glob pattern |
| `ls` | List directory contents with details |

### Memory Tools
| Tool | Description |
|------|-------------|
| `memory_search` | Text search (grep-style) over ~/.slimclaw/MEMORY.md and memory/*.md |
| `memory_get` | Read specific lines/sections from memory files |

*Note: Using simple text search to keep it lightweight (no embeddings/vector DB).*

## Directory Structure

```
slimclaw/
├── main.py                 # CLI entrypoint
├── agent.py                # Agent orchestration
├── config.json             # Settings
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
│   ├── base.py             # Common utilities
│   ├── read.py
│   ├── write.py
│   ├── edit.py
│   ├── grep.py
│   ├── find.py
│   ├── ls.py
│   ├── shell.py
│   ├── web_search.py
│   ├── memory.py           # memory_write
│   ├── memory_search.py
│   └── memory_get.py
│
└── workspace/              # Templates for setup.sh
    └── SOUL.md
```

## System Prompt Architecture

Modular builder pattern (like openclaw):

```python
# prompt/builder.py
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

Each section builder returns `str` or empty string if not applicable.

### Sections

1. **Identity** - "You are a personal assistant running inside slimclaw."
2. **Environment** - cwd, datetime, platform, user, git_branch
3. **Tooling** - Tool list with descriptions, usage guidance
4. **Behaviour** - Action over announcement, conciseness, resourcefulness
5. **Workspace** - Working directory info, file operation guidance
6. **Persona** - SOUL.md content, MEMORY.md content

## Implementation Order

1. Create `tools/` directory structure, migrate existing tools
2. Add new file tools (edit, grep, find, ls)
3. Create `prompt/` directory structure
4. Refactor system prompt into modular sections
5. Add memory tools (memory_search, memory_get)
6. Update requirements.txt if needed

## Files to Create/Modify

**New directories:**
- `tools/`
- `prompt/`

**Migrate from:**
- `tools.py` → `tools/*.py`
- `agent.py:build_system_prompt()` → `prompt/builder.py`

**New tools:**
- `tools/edit.py`
- `tools/grep.py`
- `tools/find.py`
- `tools/ls.py`
- `tools/memory_search.py`
- `tools/memory_get.py`

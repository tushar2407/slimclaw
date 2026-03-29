# SlimClaw Roadmap

## Current State (Phase 1 - Complete)

**Working features:**
- 6 tools: read, write, shell, web_search, memory, memory_search
- Modular prompt system (6 sections)
- Session persistence (JSONL)
- Shell confirmation flow
- SOUL.md / MEMORY.md personality
- Local Ollama LLM (qwen2.5:7b)
- Rich CLI with streaming UI

---

## Phase 2: Core Tool Expansion
**Complexity: LOW | Dependencies: None**

### 2.1 File Tools
- [X] `edit` - String replacement in files (old_string → new_string)
- [X] `grep` - Regex search with context lines (-A/-B/-C)
- [X] `find` - Glob pattern file search
- [X] `ls` - Directory listing with details

### 2.2 Improved Error Handling
- [X] Tool errors return structured messages
- [X] Agent retries with different approach on failure

---

## Phase 3: Configuration & Multi-Model
**Complexity: LOW-MEDIUM | Dependencies: None**

### 3.1 Enhanced Config
- [ ] YAML config support (config.yaml)
- [ ] Per-tool settings (timeouts, limits)
- [ ] Model aliases (fast/smart/creative)

### 3.2 Multi-Model Support
- [ ] Support multiple Ollama models
- [ ] Model selection per task type
- [ ] Fallback chain (if model A fails, try B)

---

## Phase 4: Heartbeats & Scheduled Tasks
**Complexity: MEDIUM | Dependencies: Phase 3**

### 4.1 Cron System
- [X] Simple cron expression parsing
- [X] Job persistence (jobs.json)
- [X] Background scheduler thread
- [ ] HEARTBEAT.md for recurring prompts

### 4.2 Wake Events
- [X] Time-based reminders
- [X] One-shot vs recurring jobs

---

## Phase 5: Browser Automation
**Complexity: MEDIUM-HIGH | Dependencies: Phase 2**

### 5.1 Basic Browser Tool
- [ ] `browser` tool using Playwright
- [ ] Navigate, click, type actions
- [ ] Screenshot capture
- [ ] Page content extraction

### 5.2 Session Management
- [ ] Persistent browser profiles
- [ ] Cookie/storage management

---

## Phase 6: Subagents
**Complexity: HIGH | Dependencies: Phase 3, 4**

### 6.1 Agent Spawning
- [X] `spawn_agent` tool to create child agents
- [X] Depth limits (prevent infinite nesting, max depth 2)
- [X] Parent-child message passing (queue-based, result returned as string)

### 6.2 Specialized Agents
- [X] AGENTS.md for defining agent types (default, researcher, coder, reader)
- [X] Per-agent tools (tool lists in AGENTS.md, shell opt-in)
- [ ] Per-agent SOUL.md (future)

---

## Phase 7: Channels (Single Channel)
**Complexity: HIGH | Dependencies: Phase 6**

### 7.1 Telegram Integration
- [ ] Bot token configuration
- [ ] Message receiving/sending
- [ ] Media handling (images, files)
- [ ] Inline commands

### 7.2 Channel Architecture
- [ ] Channel abstraction layer
- [ ] Message routing
- [ ] User authentication

---

## Phase 8: Vector Memory
**Complexity: HIGH | Dependencies: Phase 3**

### 8.1 Embeddings
- [ ] Local embeddings (sentence-transformers or Ollama)
- [ ] Chunk-based indexing
- [ ] SQLite + sqlite-vec for storage

### 8.2 Semantic Search
- [ ] Vector similarity search
- [ ] Hybrid search (keyword + semantic)
- [ ] Temporal decay (recent = more relevant)

---

## Phase 9: Plugins System
**Complexity: VERY HIGH | Dependencies: Phase 6, 7**

### 9.1 Plugin Architecture
- [ ] Plugin manifest format
- [ ] Tool registration API
- [ ] Lifecycle hooks (before/after tool calls)

### 9.2 Plugin Management
- [ ] Install/uninstall commands
- [ ] Plugin discovery
- [ ] Config persistence

---

## Phase 10: Web UI & Multi-Channel
**Complexity: VERY HIGH | Dependencies: Phase 7, 8, 9**

### 10.1 Web Interface
- [ ] CopilotKit integration
- [ ] WebSocket streaming
- [ ] Session management UI

### 10.2 Additional Channels
- [ ] Discord
- [ ] WhatsApp
- [ ] Slack
- [ ] Channel dock (multi-channel orchestration)

---

## Dependency Graph

```
Phase 1 (Done)
    ↓
Phase 2 (Tools) ──────────────────┐
    ↓                             ↓
Phase 3 (Config/Multi-Model) → Phase 5 (Browser)
    ↓
Phase 4 (Cron/Heartbeats)
    ↓
Phase 6 (Subagents)
    ↓
Phase 7 (Telegram) ←── Phase 8 (Vector Memory)
    ↓
Phase 9 (Plugins)
    ↓
Phase 10 (Web UI + Multi-Channel)
```

---

## Priority Order (Recommended)

1. **Phase 2** - File tools (immediate value, low effort)
2. **Phase 3** - Multi-model (flexibility)
3. **Phase 4** - Cron (autonomy)
4. **Phase 8** - Vector memory (smarter recall)
5. **Phase 5** - Browser (web interaction)
6. **Phase 6** - Subagents (delegation)
7. **Phase 7** - Telegram (first channel)
8. **Phase 9** - Plugins (extensibility)
9. **Phase 10** - Full platform

# OpenClaw — Project Overview

## What Is It?

OpenClaw is a **multi-channel AI agent gateway** written in TypeScript (Node.js). It bridges popular messaging platforms (WhatsApp, Telegram, Discord, iMessage, Slack, Mattermost, Signal, and more) to AI agents — primarily Anthropic's **Claude** but also OpenAI, Gemini, and any OpenAI-compatible model.

In practical terms: you send a message to a phone number or chat group, OpenClaw receives it, runs it through an AI agent, and sends the response back — all with a persistent memory and tooling layer around it.

---

## High-Level Architecture

```
User (WhatsApp/Telegram/Discord/etc.)
        │
        ▼
  Channel Adapters         ← per-platform connectors (src/whatsapp, src/telegram, etc.)
        │
        ▼
   Gateway Server          ← central HTTP + WebSocket server (src/gateway)
        │
        ▼
   Agent Runner            ← "Pi" embedded agent with tool loop (src/agents)
        │
        ▼
   LLM Provider            ← Anthropic, OpenAI, Gemini, Ollama, Bedrock, …
        │
        ▼
  Tool Execution           ← bash, browser, filesystem, web, memory, plugins
        │
        ▼
  Reply → Channel Adapter → User
```

---

## Core Concepts

### Gateway
The central server (`src/gateway/server.ts`) that everything connects to. It exposes:
- **WebSocket** for real-time streaming (agent responses, tool events)
- **HTTP REST** endpoints for config, sessions, cron, health, and a Control UI
- **OpenAI-compatible API** (`/v1/chat/completions`, `/v1/responses`) so external tools can talk to it like an OpenAI endpoint

### Channels
Each messaging platform is a "channel" with its own adapter. Channels handle auth (QR pairing for WhatsApp, bot tokens for Telegram/Discord), message normalization, media handling, and delivery. Key config: `allowFrom` lists to restrict who can trigger the agent.

### Agents ("Pi" Agents)
The agent layer (`src/agents/pi-embedded-runner`) wraps an LLM call in a **tool loop**:
1. Build a context (system prompt from workspace files + session history)
2. Call the LLM
3. If the model returns tool calls, execute them and feed results back
4. Repeat until the model returns a final text reply

"Pi" is the internal name for this agentic framework (from `@mariozechner/pi-coding-agent`). OpenClaw uses a custom tool definition layer on top.

### Tools
Every capability the agent can use is a typed "tool." Categories:
- **Filesystem/Coding**: `read`, `write`, `edit`, `apply-patch`, `bash/exec`, PTY process control
- **OpenClaw-native**: `message` (send to channels), `cron` (schedule tasks), `sessions` (spawn/list/steer subagents), `canvas`, `nodes`, `gateway`
- **Intelligence**: `web_search`, `web_fetch`, `image` (vision), `tts` (text-to-speech)
- **Plugin tools**: contributed by extensions

Tools have a **policy pipeline** — allow/deny per role, per channel, per agent scope, per tool name.

### Sessions
Each conversation (per-sender, per-group, or global) is a session stored as a JSONL transcript file. Sessions track:
- Full message history (for context window)
- Token usage
- Routing metadata (which channel, which thread)
- Compaction: when context gets too long, the session is summarized automatically

### Workspace
A directory (`~/.openclaw/workspace` by default) of markdown files that serve as the agent's long-term memory and persona:
- `SOUL.md` — persona/instructions
- `AGENTS.md` — tool/behavior config
- `MEMORY.md` — evolving memory (optional)
- `HEARTBEAT.md` — proactive task schedule
- `IDENTITY.md`, `USER.md`, `TOOLS.md`, etc.

### Plugins / Extensions
The `extensions/` directory contains plugin manifests (`openclaw.plugin.json`). Plugins can add tools, channels, auth providers, and memory backends. Key examples: `memory-lancedb` (vector memory), `talk-voice` (voice calls), `device-pair` (iOS/Android pairing), `llm-task`, `diagnostics-otel`.

### Subagents
The agent can spawn **subagents** — child sessions that run in parallel or sequentially. Subagents have their own tool scope, depth limits, and lifecycle (spawn → run → complete/fail → report back to parent). This enables multi-agent workflows inside a single conversation.

### Heartbeats
A configurable timer (default 30 min) that triggers a proactive agent run without any user message. The agent reads `HEARTBEAT.md` and decides if anything needs attention. Replies of `HEARTBEAT_OK` are silently swallowed.

---

## Key Subsystems

| Subsystem | Location | Purpose |
|---|---|---|
| Gateway server | `src/gateway/server.ts` | HTTP + WS hub |
| Channel adapters | `src/whatsapp`, `src/telegram`, `src/discord`, `src/slack`, … | Platform I/O |
| Agent runner | `src/agents/pi-embedded-runner/` | LLM tool loop |
| Tool definitions | `src/agents/tools/`, `src/agents/pi-tools.ts` | Agent capabilities |
| Config system | `src/config/` | JSON5 config with env var substitution |
| Session store | `src/agents/session-*.ts` | JSONL transcripts |
| Memory | `src/memory/`, `extensions/memory-lancedb/` | Semantic + file memory |
| Plugins | `src/plugins/`, `src/plugin-sdk/` | Extension API |
| Cron | `src/cron/`, `src/gateway/server-cron.ts` | Scheduled agent runs |
| Sandbox | `src/agents/sandbox/` | Optional filesystem isolation |
| Control UI | `src/gateway/control-ui.ts` | Web dashboard |
| CLI | `src/cli/`, `src/commands/` | `openclaw` command |
| macOS/iOS/Android apps | `apps/` | Native companion apps |

---

## Model Support

OpenClaw is model-agnostic. It supports:
- **Anthropic Claude** (native API + Bedrock)
- **OpenAI** (+ Azure, GitHub Copilot proxy)
- **Google Gemini** (+ Vertex AI)
- **Ollama** (local models)
- **HuggingFace**, **Together**, **Mistral**, **Qwen**, **MiniMax**, **Doubao**, **Venice**, and more via OpenAI-compatible base URLs
- **Auth profiles**: multiple API keys with automatic rotation and cooldown on failure

---

## Config System

Single JSON5 file at `~/.openclaw/openclaw.json`. Key sections:

```json5
{
  agent: { model: "anthropic/claude-opus-4-6", thinkingDefault: "high" },
  channels: { whatsapp: { allowFrom: ["+1..."] } },
  session: { scope: "per-sender", reset: { mode: "daily" } },
  tools: { exec: { enabled: true } },
  cron: [ { schedule: "0 9 * * *", prompt: "Daily summary" } ],
  plugins: { installed: ["memory-lancedb", "talk-voice"] }
}
```

Supports `$include` for file inclusion and `${ENV_VAR}` substitution.

---

## Native Apps

- **macOS**: Menu bar app (`apps/macos`) — starts/stops gateway, shows status, IPC via `OpenClawIPC`
- **iOS**: Swift app (`apps/ios`) — connects as a node/client via discovery protocol
- **Android**: Kotlin app (`apps/android`) — same, with Canvas UI support

Discovery uses mDNS/Bonjour (`extensions/device-pair`) so mobile apps find the Mac automatically on local network.

---

## What It Is NOT

- Not a UI chat app (that's the "WebChat" feature, a thin web client served by the gateway)
- Not an LLM itself — it's purely a gateway/orchestration layer
- Not stateless — it maintains persistent session transcripts and workspace memory

---

## Stack Summary

- **Runtime**: Node.js (TypeScript, ESM)
- **LLM client**: Anthropic SDK, OpenAI SDK, custom adapters
- **Web framework**: Custom HTTP + WebSocket server (no Express)
- **Messaging**: `whatsapp-web.js`, Telegram Bot API, Discord.js, Slack Bolt, `@signalapp/libsignal-client`, etc.
- **Storage**: Local filesystem (JSONL sessions, JSON config), optional LanceDB for vector memory
- **Packaging**: npm, also ships as a Podman/Docker container
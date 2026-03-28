"""Memory search - regex and semantic search across memory and sessions."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from slimclaw.config import MEMORY_DIR, MEMORY_FILE, SESSIONS_DIR, SLIMCLAW_DIR


def memory_write(note: str) -> str:
    """Append a note to MEMORY.md in ~/.slimclaw/."""
    SLIMCLAW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n- [{timestamp}] {note}\n"
    with open(MEMORY_FILE, "a") as f:
        f.write(entry)
    return "Memory saved."


def memory_search(
    query: str,
    semantic: bool = False,
    case_insensitive: bool = True,
    session_key: Optional[str] = None,
    top_k: int = 10,
) -> str:
    """Search memory files and session history.

    Args:
        query: Search query (regex pattern for text search, natural language for semantic)
        semantic: If True, use vector similarity search instead of regex
        case_insensitive: For regex search, ignore case (default True)
        session_key: For semantic search, optionally limit to a specific session
        top_k: For semantic search, number of results to return (default 10)

    Searches:
    - ~/.slimclaw/MEMORY.md
    - ~/.slimclaw/memory/*.md
    - ~/.slimclaw/sessions/*.jsonl (conversation history archives)

    Returns matching lines with file path and line numbers.
    """
    if semantic:
        return _semantic_search(query, session_key, top_k)

    results = []
    flags = re.IGNORECASE if case_insensitive else 0

    try:
        pattern = re.compile(query, flags)
    except re.error as e:
        return f"Invalid regex pattern: {e}"

    # Search MEMORY.md
    if MEMORY_FILE.exists():
        results.extend(_search_file(MEMORY_FILE, pattern, SLIMCLAW_DIR))

    # Search memory/*.md files
    if MEMORY_DIR.exists():
        for md_file in MEMORY_DIR.glob("*.md"):
            results.extend(_search_file(md_file, pattern, SLIMCLAW_DIR))

    # Search session messages in JSONL archives
    results.extend(_search_sessions(pattern))

    if not results:
        return f"No matches found for: {query}"

    return "\n".join(results[:50])


def _semantic_search(
    query: str, session_key: Optional[str] = None, top_k: int = 10
) -> str:
    """Perform semantic vector search across embeddings."""
    try:
        from slimclaw.memory.embeddings import (
            EmbeddingProvider,
            EmbeddingStore,
            get_embedding,
        )
    except ImportError:
        return "Embeddings module not available. Install numpy and ollama/openai."

    try:
        query_embedding = get_embedding(query, provider=EmbeddingProvider.OLLAMA)

        store = EmbeddingStore()
        results = store.search(
            query_embedding=query_embedding,
            session_key=session_key,
            top_k=top_k,
            min_similarity=0.3,
        )

        if not results:
            return f"No semantic matches found for: {query}"

        # Collect grouped indices to batch fetch content
        session_indices: dict[str, set[int]] = {}
        for r in results:
            session_indices.setdefault(r.session_key, set()).add(r.message_index)

        # Fetch contents in single passes
        contents = _get_messages_content(session_indices)

        # Format results
        output = []
        for r in results:
            content = contents.get((r.session_key, r.message_index))
            if content:
                preview = content[:200].replace("\n", " ")
                if len(content) > 200:
                    preview += "..."
                output.append(
                    f"[{r.similarity:.2f}] sessions/{r.session_key}:{r.message_index}: {preview}"
                )

        return (
            "\n".join(output) if output else f"No semantic matches found for: {query}"
        )

    except Exception as e:
        return f"Semantic search error: {e}"


def _get_messages_content(
    session_indices: dict[str, set[int]],
) -> dict[tuple[str, int], str]:
    """Get content for multiple messages across sessions efficiently."""
    contents = {}
    for session_key, indices in session_indices.items():
        if not indices:
            continue

        safe_name = session_key.replace(":", "_").replace("/", "_")
        archive_path = SESSIONS_DIR / f"{safe_name}.jsonl"

        if not archive_path.exists():
            continue

        max_index = max(indices)
        try:
            with open(archive_path) as f:
                for i, line in enumerate(f):
                    if i in indices:
                        entry = json.loads(line.strip())
                        contents[(session_key, i)] = entry.get("content", "")
                    if i >= max_index:
                        break
        except Exception:
            pass

    return contents


def _search_file(file_path: Path, pattern: re.Pattern, base_dir: Path) -> list[str]:
    """Search a single file and return matching lines."""
    matches = []
    try:
        lines = file_path.read_text().splitlines()
        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                rel_path = file_path.relative_to(base_dir)
                matches.append(f"{rel_path}:{i}: {line.strip()}")
    except Exception:
        pass
    return matches


def _search_sessions(pattern: re.Pattern) -> list[str]:
    """Search through session messages in JSONL archives."""
    matches = []

    if SESSIONS_DIR.exists():
        for jsonl_file in sorted(SESSIONS_DIR.glob("*.jsonl"), reverse=True):
            try:
                for line_num, line in enumerate(jsonl_file.read_text().splitlines(), 1):
                    try:
                        entry = json.loads(line)
                        content = entry.get("content", "")
                        if pattern.search(content):
                            role = entry.get("role", "?")
                            preview = content[:300].replace("\n", " ")
                            if len(content) > 300:
                                preview += "..."
                            matches.append(
                                f"sessions/{jsonl_file.name}:{line_num}: [{role}] {preview}"
                            )
                    except json.JSONDecodeError:
                        continue
            except Exception:
                pass

    return matches


def memory_get(path: str = "MEMORY.md", line_range: str = "") -> str:
    """Read from a memory file, optionally a specific line range.

    Args:
        path: Path relative to ~/.slimclaw/ (e.g. "MEMORY.md" or "memory/notes.md").
        line_range: Optional line specifier (e.g. "1-50", "10", "10,20,30")

    Returns:
        File contents for the requested range, or an error message.
    """
    target = (SLIMCLAW_DIR / path).resolve()
    if not target.resolve().is_relative_to(SLIMCLAW_DIR.resolve()):
        return f"Path must be under ~/.slimclaw/: {path}"

    if not target.exists():
        return f"Memory file not found: {path}"

    try:
        lines = target.read_text().splitlines()
    except Exception as e:
        return f"Could not read file: {e}"

    total = len(lines)
    if total == 0:
        return f"File is empty: {path}"

    if not line_range or not line_range.strip():
        return "\n".join(lines)

    # Parse line_range: "1-50" or "10" or "10,20,30"
    indices: set[int] = set()
    for part in re.split(r"[,;]\s*", line_range.strip()):
        part = part.strip()
        if "-" in part:
            try:
                a, b = part.split("-", 1)
                start, end = int(a.strip()), int(b.strip())
                for i in range(max(1, start), min(total, end) + 1):
                    indices.add(i)
            except ValueError:
                continue
        else:
            try:
                i = int(part)
                if 1 <= i <= total:
                    indices.add(i)
            except ValueError:
                continue

    if not indices:
        return f"Invalid line range: {line_range}. File has {total} lines."

    result_lines = [lines[i - 1] for i in sorted(indices)]
    return "\n".join(result_lines)

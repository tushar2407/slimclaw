"""Web search tool - search the web via DuckDuckGo."""

from ddgs import DDGS
from langchain_core.tools import StructuredTool

from .types import err, ok


def web_search(query: str) -> str:
    """Search the web using DuckDuckGo."""
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return ok("No results found.")
        return ok(
            "\n\n".join(f"{r['title']}\n{r['href']}\n{r['body']}" for r in results)
        )
    except Exception as e:
        return err(f"Search failed: {e}", "search_error")


tool = StructuredTool.from_function(
    web_search, name="web_search", description="Search the web using DuckDuckGo."
)

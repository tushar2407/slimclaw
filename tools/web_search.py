"""Web search tool - search the web via DuckDuckGo."""
from ddgs import DDGS
from langchain_core.tools import StructuredTool


def web_search(query: str) -> str:
    """Search the web using DuckDuckGo."""
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return "No results found."
        return "\n\n".join(
            f"{r['title']}\n{r['href']}\n{r['body']}" for r in results
        )
    except Exception as e:
        return f"Search error: {e}"


tool = StructuredTool.from_function(
    web_search,
    name="web_search",
    description="Search the web using DuckDuckGo."
)

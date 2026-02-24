"""Tools package - exports TOOLS list for the agent."""

from .read import tool as read_tool
from .write import tool as write_tool
from .shell import tool as shell_tool
from .web_search import tool as web_search_tool
from .memory import memory_write_tool, memory_search_tool, memory_get_tool

TOOLS = [
    read_tool,
    write_tool,
    shell_tool,
    web_search_tool,
    memory_write_tool,
    memory_search_tool,
    memory_get_tool,
]

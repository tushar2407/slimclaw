"""Tools package - exports TOOLS list for the agent."""

from slimclaw.tools.read import tool as read_tool
from slimclaw.tools.write import tool as write_tool
from slimclaw.tools.shell import tool as shell_tool
from slimclaw.tools.web_search import tool as web_search_tool
from slimclaw.tools.memory import (
    memory_write_tool,
    memory_search_tool,
    memory_get_tool,
)
from slimclaw.tools.edit import tool as edit_tool
from slimclaw.tools.grep import tool as grep_tool
from slimclaw.tools.find import tool as find_tool
from slimclaw.tools.ls import tool as ls_tool

TOOLS = [
    read_tool,
    write_tool,
    shell_tool,
    web_search_tool,
    memory_write_tool,
    memory_search_tool,
    memory_get_tool,
    edit_tool,
    grep_tool,
    find_tool,
    ls_tool,
]

__all__ = ["TOOLS"]

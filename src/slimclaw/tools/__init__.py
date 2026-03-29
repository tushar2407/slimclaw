"""Tools package - exports TOOLS list for the agent."""

from slimclaw.tools.cron import cancel_reminder, list_reminders, schedule_reminder
from slimclaw.tools.edit import edit
from slimclaw.tools.find import find
from slimclaw.tools.grep import grep
from slimclaw.tools.ls import ls
from slimclaw.tools.memory import memory_get, memory_search, memory_write
from slimclaw.tools.read import read
from slimclaw.tools.shell import shell
from slimclaw.tools.web_search import web_search
from slimclaw.tools.write import write

TOOLS = [
    read,
    write,
    shell,
    web_search,
    memory_write,
    memory_search,
    memory_get,
    edit,
    grep,
    find,
    ls,
    schedule_reminder,
    list_reminders,
    cancel_reminder,
]

__all__ = ["TOOLS"]

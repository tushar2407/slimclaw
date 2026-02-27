from datetime import datetime
from pathlib import Path

from langchain_core.tools import StructuredTool

from slimclaw.tools.base import resolve_path


def _format_mode(mode: int, is_dir: bool) -> str:
    """Format file mode bits similarly to `ls -l`."""
    perms = ["d" if is_dir else "-"]
    for shift in (6, 3, 0):
        m = (mode >> shift) & 0b111
        perms.append("r" if m & 0b100 else "-")
        perms.append("w" if m & 0b010 else "-")
        perms.append("x" if m & 0b001 else "-")
    return "".join(perms)


def ls(path: str = ".", long: bool = False) -> str:
    """List directory contents. Use long=True for detailed output (mode, size, mtime)."""
    target = resolve_path(path)

    if not target.exists():
        return f"Path not found: {path}"

    if target.is_file():
        items = [target]
    # if directory
    else:
        try:
            items = sorted(
                target.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except Exception as e:
            return f"Could not list directory: {e}"

    lines = []
    for p in items:
        name = p.name + ("/" if p.is_dir() else "")

        if long:
            try:
                st = p.stat()
            except OSError:
                continue
            mode = _format_mode(st.st_mode, p.is_dir())
            size = st.st_size
            mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
            lines.append(f"{mode} {size:>8} {mtime} {name}")
        else:
            lines.append(name)

    return "\n".join(lines) if lines else "(empty)"


tool = StructuredTool.from_function(
    ls,
    name="ls",
    description="Directory listing. Use long=True for details (mode, size, mtime). Defaults to names only.",
)


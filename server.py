"""FastAPI server for slimclaw chatbot web UI."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, AIMessage
from agent import run_agent
from tools.shell import allow_next_shell

APP_DIR = Path(__file__).parent
STATIC_DIR = APP_DIR / "static"


class ChatRequest(BaseModel):
    message: str
    history: list[dict]  # [{"role": "user"|"assistant", "content": "..."}]
    shell_confirm: bool = False


class ChatResponse(BaseModel):
    content: str
    needs_shell_confirm: bool = False
    shell_command: str | None = None


def _history_to_messages(history: list[dict]):
    msgs = []
    for h in history:
        role, content = h.get("role", ""), h.get("content", "")
        if role == "user":
            msgs.append(HumanMessage(content=content))
        elif role == "assistant":
            msgs.append(AIMessage(content=content))
    return msgs


@asynccontextmanager
async def lifespan(app: FastAPI):
    STATIC_DIR.mkdir(exist_ok=True)
    yield


app = FastAPI(title="SlimClaw Chat", lifespan=lifespan)


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Send a message and get the agent's response."""
    chat_history = _history_to_messages(request.history)

    if request.shell_confirm:
        allow_next_shell(True)
        # Last message is the user message we're retrying - strip it so run_agent doesn't duplicate
        if chat_history and isinstance(chat_history[-1], HumanMessage):
            user_input = chat_history[-1].content
            chat_history = chat_history[:-1]
        else:
            user_input = request.message
    else:
        user_input = request.message

    response, extra = run_agent(user_input, chat_history)

    if response == "__SHELL_CONFIRM__":
        command = extra.get("command", "") if extra else ""
        return ChatResponse(content="", needs_shell_confirm=True, shell_command=command)
    return ChatResponse(content=response, needs_shell_confirm=False)


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

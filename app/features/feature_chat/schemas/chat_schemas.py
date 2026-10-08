# Pydantic models for the /ws/chat wire protocol (see README.md protocol spec).
from pydantic import BaseModel


class IncomingMessage(BaseModel):
    """Anything the client sends: either {"type": "auth", "token": ...}
    or {"type": "message", "text": ...}."""
    type: str
    text: str | None = None
    token: str | None = None


class StreamEvent(BaseModel):
    """One chunk of a streamed bot reply."""
    type: str = "stream"
    text: str


class DoneEvent(BaseModel):
    """Signals the end of a streamed reply."""
    type: str = "done"


class ErrorEvent(BaseModel):
    """Sent when the LLM or a tool call fails; the connection stays open."""
    type: str = "error"
    message: str

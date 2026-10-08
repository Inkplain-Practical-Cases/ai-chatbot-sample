# Thin door for the chat feature: declares the /ws/chat route, injects the
# shared provider singletons, and immediately delegates to the handler.
# No auth/streaming/business logic should live here.
from fastapi import APIRouter, Depends, WebSocket

from app.core.dependencies import get_embedder, get_llm_provider, get_vectorstore
from app.features.feature_chat.handlers.handle_chat_socket import handle_chat_socket

router = APIRouter()


@router.websocket("/ws/chat")
async def chat_socket(
    websocket: WebSocket,
    embedder=Depends(get_embedder),
    store=Depends(get_vectorstore),
    llm=Depends(get_llm_provider),
) -> None:
    """Websocket route for /ws/chat. FastAPI resolves the three provider
    singletons via Depends(...) and hands them straight to the handler."""
    await handle_chat_socket(websocket, embedder, store, llm)

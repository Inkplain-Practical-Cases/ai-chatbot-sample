# Orchestrates the whole /ws/chat lifecycle: accept -> auth handshake ->
# message loop -> stream reply. Called by router.py, never called directly
# by a route (keeps router.py a thin door).
from fastapi import WebSocket, WebSocketDisconnect

from app.core.config import get_settings
from app.features.feature_auth.services.service_verify_jwt import AuthError, service_verify_jwt
from app.features.feature_chat.schemas.chat_schemas import IncomingMessage
from app.features.feature_chat.services.service_retrieve_chunks import service_retrieve_chunks
from app.features.feature_chat.services.service_stream_llm import service_stream_llm
from app.providers.embeddings.sentence_transformers_provider import SentenceTransformersProvider
from app.providers.llm.base import LLMProvider
from app.providers.vectorstore.chroma_store import ChromaStore


async def handle_chat_socket(
    websocket: WebSocket,
    embedder: SentenceTransformersProvider,
    store: ChromaStore,
    llm: LLMProvider,
) -> None:
    """Drives one /ws/chat connection end to end: accepts the socket, requires
    a valid auth message before anything else happens, then loops forever
    answering each incoming message until the client disconnects."""
    await websocket.accept()

    # Step 1: auth handshake. The client must send {"type": "auth", "token": ...}
    # first. The JWT is verified against JWT_SECRET (see .env) and its claims
    # (department, level) become this connection's identity for RBAC filtering.
    try:
        raw_auth = await websocket.receive_json()
        auth_msg = IncomingMessage(**raw_auth)
    except WebSocketDisconnect:
        return
    except Exception:
        await websocket.send_json({"type": "auth_failed", "message": "invalid auth message"})
        await websocket.close()
        return

    if auth_msg.type != "auth" or not auth_msg.token:
        await websocket.send_json({"type": "auth_failed", "message": "expected auth message with token"})
        await websocket.close()
        return

    try:
        user = service_verify_jwt(auth_msg.token, get_settings())
    except AuthError as exc:
        await websocket.send_json({"type": "auth_failed", "message": str(exc)})
        await websocket.close()
        return

    await websocket.send_json({
        "type": "auth_success",
        "user_id": user.sub,
        "department": user.department,
        "level": user.level,
    })

    # Step 2: message loop. Every {"type": "message", "text": ...} triggers an
    # RBAC-filtered retrieval against Chroma, then the matched chunks are
    # passed to the LLM as context and its answer is streamed token by token.
    # A retrieval or LLM failure sends a user-facing "error" event but keeps
    # the connection open, per README requirement 7.
    try:
        while True:
            try:
                raw = await websocket.receive_json()
                msg = IncomingMessage(**raw)
            except WebSocketDisconnect:
                raise
            except Exception as exc:
                await websocket.send_json({"type": "error", "message": f"invalid message: {exc}"})
                continue

            if msg.type != "message" or not msg.text:
                continue

            try:
                chunks = await service_retrieve_chunks(
                    text=msg.text,
                    department=user.department,
                    level=user.level,
                    embedder=embedder,
                    store=store,
                )
                async for token in service_stream_llm(msg.text, chunks, llm, user.sub):
                    await websocket.send_json({"type": "stream", "text": token})
                await websocket.send_json({"type": "done"})
            except Exception as exc:
                await websocket.send_json({"type": "error", "message": f"failed to answer: {exc}"})
    except WebSocketDisconnect:
        pass

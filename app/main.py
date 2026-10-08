# Entry point of the backend. Builds the FastAPI app and wires up feature
# routers. This file must stay a "thin door" — no business logic here.
from fastapi import FastAPI

from app.features.feature_chat.router import router as chat_router

app = FastAPI(title="Mini RAG Chatbot")

# Registers the /ws/chat websocket route defined in feature_chat/router.py.
app.include_router(chat_router)

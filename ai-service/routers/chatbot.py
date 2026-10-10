"""
Chatbot API router — RAG + OpenAI + Streaming.
"""
import json
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional

from chatbot.chat_engine import chat, build_messages, client, MODEL, MAX_TOKENS, TEMPERATURE
from chatbot.vector_store import vector_store
from chatbot.tools import TOOLS_SCHEMA, execute_tool

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    user_context: Optional[dict] = {}
    auth_token: Optional[str] = ''


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list = []
    sources: list = []


@router.post("/ask", response_model=ChatResponse)
def ask(req: ChatRequest):
    """Non-streaming chat."""
    if not req.message.strip():
        raise HTTPException(400, "Empty message")

    result = chat(
        user_message=req.message,
        user_context=req.user_context,
        auth_token=req.auth_token,
        history=[h.dict() for h in req.history],
    )
    return result


@router.post("/stream")
def stream_chat(req: ChatRequest):
    """SSE streaming chat."""
    if not req.message.strip():
        raise HTTPException(400, "Empty message")

    def event_stream():
        try:
            messages = build_messages(
                req.message,
                req.user_context,
                [h.dict() for h in req.history],
            )
            sources = [r['source'] for r in vector_store.search(req.message, top_k=4)]

            # Send sources metadata first
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

            for _ in range(3):
                stream = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=TOOLS_SCHEMA,
                    tool_choice='auto',
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                    stream=True,
                )

                tool_calls_buffer = {}
                assistant_text = ''

                for chunk in stream:
                    delta = chunk.choices[0].delta

                    if delta.content:
                        assistant_text += delta.content
                        yield f"data: {json.dumps({'type': 'token', 'content': delta.content})}\n\n"

                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_buffer:
                                tool_calls_buffer[idx] = {
                                    'id': '', 'name': '', 'arguments': ''
                                }
                            if tc.id:
                                tool_calls_buffer[idx]['id'] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    tool_calls_buffer[idx]['name'] = tc.function.name
                                if tc.function.arguments:
                                    tool_calls_buffer[idx]['arguments'] += tc.function.arguments

                # If no tool calls — we're done
                if not tool_calls_buffer:
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    return

                # Execute tools
                messages.append({
                    "role": "assistant",
                    "content": assistant_text or "",
                    "tool_calls": [
                        {
                            "id": tc['id'],
                            "type": "function",
                            "function": {
                                "name": tc['name'],
                                "arguments": tc['arguments'],
                            }
                        } for tc in tool_calls_buffer.values()
                    ],
                })

                for tc in tool_calls_buffer.values():
                    yield f"data: {json.dumps({'type': 'tool', 'name': tc['name']})}\n\n"
                    args = json.loads(tc['arguments'] or '{}')
                    result = execute_tool(tc['name'], args, req.auth_token)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc['id'],
                        "content": json.dumps(result, ensure_ascii=False),
                    })

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/rebuild-index")
def rebuild_index():
    """Rebuild FAISS index from knowledge base."""
    vector_store.build(force=True)
    return {'status': 'rebuilt', 'chunks': len(vector_store.chunks)}


@router.get("/health")
def chatbot_health():
    return {
        'status': 'ok',
        'model': MODEL,
        'kb_chunks': len(vector_store.chunks),
        'index_loaded': vector_store.index is not None,
    }
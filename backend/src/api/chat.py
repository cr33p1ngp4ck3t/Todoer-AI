"""Chat API endpoints with SSE streaming support."""

import json
import logging
from typing import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session
from src.api.auth import get_current_user
from src.lib.database import get_session
from src.models.user import User
from src.services.chatbot_service import ChatbotService
from src.services.mcp_server import MCPToolHandler
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger("todo-api")
router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Request model for chat messages."""

    message: str
    conversation_id: UUID | None = None


class ToolCallRequest(BaseModel):
    """Request model for tool calls from client."""

    tool_name: str
    arguments: dict


async def chat_stream(
    user_id: UUID,
    message: str,
    conversation_id: UUID | None,
    session: Session,
) -> AsyncIterator[str]:
    """Generate streaming response for chat.

    Args:
        user_id: UUID of the authenticated user
        message: User's message content
        conversation_id: Optional existing conversation ID
        session: Database session

    Yields:
        SSE-formatted string chunks
    """
    try:
        chatbot = ChatbotService(
            user_id=user_id,
            session=session,
        )

        # Stream the LLM response
        async for chunk in chatbot.chat(
            message=message,
            conversation_id=conversation_id,
            stream=True,
        ):
            # Format as SSE event
            if hasattr(chunk, "choices") and chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    yield f"data: {json.dumps({'type': 'content', 'content': delta.content})}\n\n"

            # Check for tool calls
            if hasattr(chunk, "choices") and chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        tool_data = {
                            "type": "tool_call",
                            "data": {
                                "id": tool_call.id,
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments,
                                },
                            },
                        }
                        yield f"data: {json.dumps(tool_data)}\n\n"

        # Send done signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        logger.error(f"Chat stream error: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


@router.post("")
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Send a chat message and receive streaming response.

    Args:
        request: ChatRequest with message and optional conversation_id
        current_user: Authenticated user from JWT
        session: Database session

    Returns:
        StreamingResponse with SSE events
    """
    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty"
        )

    logger.info(f"Chat request from user {current_user.id}: {request.message[:100]}...")

    return EventSourceResponse(
        chat_stream(
            user_id=current_user.id,
            message=request.message,
            conversation_id=request.conversation_id,
            session=session,
        ),
        media_type="text/event-stream",
    )


@router.post("/tool-call")
async def execute_tool_call(
    tool_request: ToolCallRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Execute a tool call directly (for client-side tool handling).

    Args:
        tool_request: ToolCallRequest with tool_name and arguments
        current_user: Authenticated user from JWT
        session: Database session

    Returns:
        JSON response with tool execution result
    """
    mcp_handler = MCPToolHandler(
        user_id=current_user.id,
        session=session,
    )

    result = mcp_handler.execute_tool(
        tool_name=tool_request.tool_name,
        arguments=tool_request.arguments,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )

    return result


class SmartParseRequest(BaseModel):
    """Request model for smart task parsing."""

    text: str


@router.post("/smart-parse")
async def smart_parse_task(
    request: SmartParseRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Parse natural language into a structured task.

    Args:
        request: SmartParseRequest with natural language text
        current_user: Authenticated user from JWT
        session: Database session

    Returns:
        Structured task details
    """
    if not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Text cannot be empty"
        )

    chatbot = ChatbotService(
        user_id=current_user.id,
        session=session,
    )

    result = await chatbot.smart_parse_task(request.text)
    return result


@router.get("/health")
async def chat_health():
    """Check chat service health."""
    return {"status": "healthy", "service": "chat-api"}

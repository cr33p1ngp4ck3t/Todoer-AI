"""Chatbot orchestration service.

This module coordinates the LLM providers, MCP tools, and conversation
management to provide a unified chatbot interface with streaming support.
"""

import json
import asyncio
from typing import AsyncIterator, Dict, Any, List, Optional, Tuple
from uuid import UUID
from sqlmodel import Session
from src.services.llm_providers import LLMProvider, LLMProviderManager
from src.services.groq_client import GroqClient
from src.services.gemini_client import GeminiClient
from src.services.mcp_server import MCPToolHandler, get_mcp_tools
from src.models.conversation import Conversation
from src.models.message import Message
import logging

logger = logging.getLogger("todo-api")


class ChatbotService:
    """Orchestrates chatbot interactions with LLM providers and MCP tools."""

    # System prompt that defines the AI assistant's personality and capabilities
    SYSTEM_PROMPT = """You are a helpful AI assistant for managing a user's todo list.

Your personality:
- Friendly, concise, and action-oriented
- You help users manage their tasks through natural conversation
- You confirm actions before executing them when appropriate

Your capabilities:
1. **Add tasks**: Create new tasks with title, description, priority, and tags
2. **List tasks**: Show user's tasks with optional filtering
3. **Update tasks**: Modify task details like title, description, priority, or tags
4. **Complete tasks**: Mark tasks as done
5. **Delete tasks**: Remove tasks permanently
6. **Search tasks**: Find tasks by keyword in title or description
7. **Suggest breakdown**: Break down complex tasks into smaller subtasks

Guidelines:
- Use tools to perform actions rather than just describing them
- When creating tasks, suggest sensible defaults (medium priority, no tags unless specified)
- After completing actions, summarize what was done
- If asked to modify a non-existent task, ask the user to clarify which task they mean
- Keep responses conversational but concise
- Always respond in the same language the user uses

Remember: You have access to the user's actual task data through your tools."""

    def __init__(
        self,
        user_id: UUID,
        session: Session,
        provider_manager: Optional[LLMProviderManager] = None,
    ):
        """Initialize chatbot service.

        Args:
            user_id: UUID of the authenticated user
            session: SQLModel database session
            provider_manager: Optional provider manager (defaults to global)
        """
        self.user_id = user_id
        self.session = session
        self.provider_manager = provider_manager or LLMProviderManager()
        self.mcp_handler = MCPToolHandler(user_id=user_id, session=session)
        self.mcp_tools = get_mcp_tools()

    async def get_provider_client(
        self,
        preferred_provider: Optional[LLMProvider] = None,
    ) -> Tuple[Any, LLMProvider]:
        """Get an available LLM provider client with fallback.

        Args:
            preferred_provider: Preferred provider (uses default if not specified)

        Returns:
            Tuple of (client, provider_type)
        """
        # Get primary and fallback configs
        primary_config, fallback_config = (
            self.provider_manager.get_primary_with_fallback()
        )

        if primary_config is None:
            raise ValueError(
                "No LLM provider is configured. Please set GROQ_API_KEY or GEMINI_API_KEY."
            )

        # Try preferred provider first
        provider_to_try = (
            preferred_provider or self.provider_manager.get_default_provider()
        )

        if (
            provider_to_try == LLMProvider.GROQ
            and primary_config.provider == LLMProvider.GROQ
        ):
            client = await self._create_groq_client(primary_config)
            return client, LLMProvider.GROQ

        if (
            provider_to_try == LLMProvider.GEMINI
            and primary_config.provider == LLMProvider.GEMINI
        ):
            client = self._create_gemini_client(primary_config)
            return client, LLMProvider.GEMINI

        # Try primary config's provider
        if primary_config.provider == LLMProvider.GROQ:
            try:
                client = await self._create_groq_client(primary_config)
                return client, LLMProvider.GROQ
            except Exception as e:
                logger.warning(f"Failed to create Groq client: {e}")

        # Try fallback provider
        if fallback_config:
            if fallback_config.provider == LLMProvider.GEMINI:
                client = self._create_gemini_client(fallback_config)
                return client, LLMProvider.GEMINI

        # Fallback to primary if it wasn't tried yet
        if primary_config.provider == LLMProvider.GEMINI:
            client = self._create_gemini_client(primary_config)
            return client, LLMProvider.GEMINI

        raise ValueError("Failed to create any LLM client. Please check your API keys.")

    async def _create_groq_client(self, config) -> GroqClient:
        """Create Groq client asynchronously."""
        client = await create_groq_client(
            api_key=config.api_key,
            model=config.model,
        )
        if client is None:
            raise ValueError("Groq API key not configured")
        return client

    def _create_gemini_client(self, config) -> GeminiClient:
        """Create Gemini client."""
        client = create_gemini_client(
            api_key=config.api_key,
            model=config.model,
        )
        if client is None:
            raise ValueError("Gemini API key not configured")
        return client

    async def smart_parse_task(self, text: str) -> Dict[str, Any]:
        """Parse natural language task description into a structured Task object.

        Args:
            text: Natural language task description

        Returns:
            Dictionary with task fields (title, description, priority, tags, status)
        """
        prompt = f"""Extract task details from this text: "{text}"
        Return ONLY valid JSON with these keys:
        - title: string (required)
        - description: string (optional, null if empty)
        - priority: string (low, medium, high - default medium)
        - tags: list of strings (optional)
        - status: string (pending)

        Respond with JSON ONLY."""

        client, provider = await self.get_provider_client()

        try:
            messages = [
                {"role": "system", "content": "You are a helpful task parser."},
                {"role": "user", "content": prompt},
            ]

            # Using simple chat (no stream) for parsing
            response_gen = client.chat(messages=messages, stream=False)
            response = await anext(response_gen)

            content = ""
            if provider == LLMProvider.GROQ:
                content = response.choices[0].message.content
            elif provider == LLMProvider.GEMINI:
                # Gemini structure varies depending on SDK version
                if hasattr(response, "text"):
                    content = response.text
                elif hasattr(response, "choices"):
                    content = response.choices[0].message.content

            # Clean JSON string (remove markdown blocks if present)
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()

            parsed = json.loads(content)

            # Validate priority
            if "priority" in parsed and parsed["priority"] not in [
                "low",
                "medium",
                "high",
            ]:
                parsed["priority"] = "medium"

            return parsed

        except Exception as e:
            logger.error(f"Smart parse error: {e}", exc_info=True)
            # Fallback to simple extraction
            return {
                "title": text[:100],
                "description": text,
                "priority": "medium",
                "status": "pending",
                "tags": [],
            }
        finally:
            if hasattr(client, "close"):
                await client.close()

    async def chat(
        self,
        message: str,
        conversation_id: Optional[UUID] = None,
        stream: bool = True,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Process a chat message and yield streaming responses.

        Args:
            message: User's message content
            conversation_id: Optional existing conversation ID
            stream: Whether to stream the response

        Yields:
            Dictionary containing response chunks or tool calls
        """
        logger.info(f"Processing chat message for user {self.user_id}")

        # Get or create conversation
        conversation = await self._get_or_create_conversation(conversation_id)

        # Save user message
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=message,
        )
        self.session.add(user_msg)
        self.session.commit()

        # Build message history (limit to last 20 messages for context window)
        messages = await self._build_message_history(conversation.id)

        # Get LLM client with fallback
        client, provider = await self.get_provider_client()

        try:
            # Stream response from LLM
            async for chunk in client.chat(
                messages=messages,
                tools=self.mcp_tools,
                stream=stream,
            ):
                yield chunk

            # Note: In a real implementation, you'd parse the response
            # to detect tool calls and execute them. For now, this is
            # a simplified version that sends the message and returns
            # the LLM response.

        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            yield {"error": str(e)}
        finally:
            if hasattr(client, "close"):
                await client.close()

    async def _get_or_create_conversation(
        self,
        conversation_id: Optional[UUID],
    ) -> Conversation:
        """Get existing conversation or create new one."""
        if conversation_id:
            conversation = self.session.get(Conversation, conversation_id)
            if conversation and conversation.user_id == self.user_id:
                return conversation

        # Create new conversation
        conversation = Conversation(
            user_id=self.user_id,
            title=None,  # Will be set based on first message
        )
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    async def _build_message_history(
        self,
        conversation_id: UUID,
        max_messages: int = 20,
    ) -> List[Dict[str, str]]:
        """Build message history for LLM context.

        Args:
            conversation_id: Conversation to load messages from
            max_messages: Maximum number of messages to include

        Returns:
            List of message dictionaries with role and content
        """
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        # Get recent messages
        result = self.session.exec(
            Message.__table__.select()
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(max_messages)
        )
        recent_messages = result.all()
        recent_messages.reverse()  # Oldest first

        for msg in recent_messages:
            messages.append(
                {
                    "role": msg.role,
                    "content": msg.content,
                }
            )

        return messages

    async def execute_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute an MCP tool call.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments dictionary

        Returns:
            Tool execution result
        """
        return self.mcp_handler.execute_tool(tool_name, arguments)


# Import helper functions at module level
from src.services.groq_client import create_groq_client
from src.services.gemini_client import create_gemini_client

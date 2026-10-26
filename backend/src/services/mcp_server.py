"""MCP (Model Context Protocol) Server for AI chatbot tool definitions.

This module defines the tools available to the LLM for task management.
Each tool has a JSON schema for validation and a handler function.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlmodel import Session
from src.services.task_service import TaskService
import logging

logger = logging.getLogger("todo-api")

# MCP Tool Definitions (JSON Schema format for LLMs)
MCP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Create a new task with optional description, priority, and tags",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Task title (1-255 characters)",
                        "minLength": 1,
                        "maxLength": 255,
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional task description (max 1000 characters)",
                        "maxLength": 1000,
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Task priority level",
                        "default": "medium",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string", "maxLength": 50},
                        "description": "Optional list of tags (lowercase, max 50 chars each)",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "Retrieve tasks with optional filters for status, priority, search query, and sorting",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "completed", "all"],
                        "description": "Filter by task status",
                        "default": "all",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Filter by priority level",
                    },
                    "search": {
                        "type": "string",
                        "description": "Search query for title and description",
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["created_at", "priority"],
                        "description": "Sort order for results",
                        "default": "created_at",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Modify an existing task's fields (title, description, priority, tags)",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "UUID of the task to update",
                        "format": "uuid",
                    },
                    "title": {
                        "type": "string",
                        "description": "New task title",
                        "minLength": 1,
                        "maxLength": 255,
                    },
                    "description": {
                        "type": "string",
                        "description": "New task description",
                        "maxLength": 1000,
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "New priority level",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string", "maxLength": 50},
                        "description": "New tags (replaces all existing)",
                    },
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a task as completed",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "UUID of the task to complete",
                        "format": "uuid",
                    }
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Permanently delete a task",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "UUID of the task to delete",
                        "format": "uuid",
                    }
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_tasks",
            "description": "Natural language search across all tasks (title and description)",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                        "minLength": 1,
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_breakdown",
            "description": "AI-powered task breakdown - suggest 3-5 smaller subtasks for a complex task",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Description of the complex task to break down",
                        "minLength": 1,
                        "maxLength": 1000,
                    }
                },
                "required": ["task_description"],
            },
        },
    },
]


class MCPToolHandler:
    """Handler for executing MCP tool calls from LLM."""

    def __init__(self, user_id: UUID, session: Session):
        """Initialize handler with user context and database session.

        Args:
            user_id: UUID of the authenticated user
            session: SQLModel database session
        """
        self.user_id = user_id
        self.session = session
        self.task_service = TaskService(user_id=user_id)

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call and return the result.

        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments for the tool

        Returns:
            Dictionary with tool execution result

        Raises:
            ValueError: If tool_name is not recognized
        """
        logger.info(f"Executing tool '{tool_name}' with args: {arguments}")

        handlers = {
            "add_task": self._handle_add_task,
            "list_tasks": self._handle_list_tasks,
            "update_task": self._handle_update_task,
            "complete_task": self._handle_complete_task,
            "delete_task": self._handle_delete_task,
            "search_tasks": self._handle_search_tasks,
            "suggest_breakdown": self._handle_suggest_breakdown,
        }

        handler = handlers.get(tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {tool_name}")

        try:
            result = handler(arguments)
            logger.info(f"Tool '{tool_name}' executed successfully")
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Tool '{tool_name}' failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _handle_add_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle add_task tool call."""
        task = self.task_service.create(
            session=self.session,
            title=args["title"],
            description=args.get("description"),
            priority=args.get("priority", "medium"),
            tags=args.get("tags"),
        )

        # Fetch tags for response
        from sqlmodel import select
        from src.models.task import Tag

        tags = self.session.exec(select(Tag).where(Tag.task_id == task.id)).all()
        tag_names = [tag.name for tag in tags]

        return {
            "task_id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "tags": tag_names,
            "created_at": task.created_at.isoformat(),
        }

    def _handle_list_tasks(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list_tasks tool call."""
        status = args.get("status", "all")
        # Convert "all" to None for TaskService
        status_filter = None if status == "all" else status

        tasks = self.task_service.get_all(
            session=self.session,
            search=args.get("search"),
            status=status_filter,
            priority=args.get("priority"),
            sort_by=args.get("sort_by", "created_at"),
        )

        # Format tasks with tags
        from sqlmodel import select
        from src.models.task import Tag

        task_list = []
        for task in tasks:
            tags = self.session.exec(select(Tag).where(Tag.task_id == task.id)).all()
            tag_names = [tag.name for tag in tags]

            task_list.append(
                {
                    "id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "tags": tag_names,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                }
            )

        return {
            "tasks": task_list,
            "count": len(task_list),
        }

    def _handle_update_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle update_task tool call."""
        task_id = UUID(args["task_id"])

        task = self.task_service.update(
            task_id=task_id,
            session=self.session,
            title=args.get("title"),
            description=args.get("description"),
            priority=args.get("priority"),
            tags=args.get("tags"),
        )

        if not task:
            raise ValueError(f"Task {task_id} not found or access denied")

        # Fetch tags for response
        from sqlmodel import select
        from src.models.task import Tag

        tags = self.session.exec(select(Tag).where(Tag.task_id == task.id)).all()
        tag_names = [tag.name for tag in tags]

        return {
            "task_id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "tags": tag_names,
            "updated_at": task.updated_at.isoformat(),
        }

    def _handle_complete_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle complete_task tool call."""
        task_id = UUID(args["task_id"])

        task = self.task_service.update(
            task_id=task_id,
            session=self.session,
            status="completed",
        )

        if not task:
            raise ValueError(f"Task {task_id} not found or access denied")

        return {
            "task_id": str(task.id),
            "title": task.title,
            "status": task.status,
            "updated_at": task.updated_at.isoformat(),
        }

    def _handle_delete_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delete_task tool call."""
        task_id = UUID(args["task_id"])

        success = self.task_service.delete(task_id=task_id, session=self.session)

        if not success:
            raise ValueError(f"Task {task_id} not found or access denied")

        return {
            "task_id": str(task_id),
            "status": "deleted",
        }

    def _handle_search_tasks(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search_tasks tool call (wrapper around list_tasks with search)."""
        return self._handle_list_tasks({"search": args["query"], "status": "all"})

    def _handle_suggest_breakdown(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle suggest_breakdown tool call.

        This is a placeholder for AI-powered task breakdown.
        In Phase 6, this will call an LLM to generate subtask suggestions.
        For now, it returns a simple rule-based breakdown.
        """
        task_description = args["task_description"]

        # TODO (Phase 6): Implement AI-powered breakdown using Grok/Gemini
        # For now, return a placeholder response
        suggestions = [
            {
                "title": f"Research and plan: {task_description[:50]}",
                "priority": "high",
                "tags": ["planning"],
            },
            {
                "title": f"Implement core functionality for: {task_description[:40]}",
                "priority": "high",
                "tags": ["development"],
            },
            {
                "title": f"Test and validate: {task_description[:50]}",
                "priority": "medium",
                "tags": ["testing"],
            },
        ]

        return {
            "original_task": task_description,
            "suggestions": suggestions,
            "note": "AI-powered breakdown will be enhanced in Phase 6",
        }


def get_mcp_tools() -> List[Dict[str, Any]]:
    """Get the list of MCP tool definitions for LLM.

    Returns:
        List of tool definitions in OpenAI function calling format
    """
    return MCP_TOOLS

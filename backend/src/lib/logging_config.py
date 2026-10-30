"""Shared JSON logging and per-request context for all application loggers."""

import logging
from contextvars import ContextVar
from uuid import UUID, uuid4

from src.lib.logging import JSONFormatter

request_context: ContextVar[dict | None] = ContextVar("request_context", default=None)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        context = request_context.get() or {}
        for key in ("request_id", "user_id"):
            if not hasattr(record, key):
                setattr(record, key, context.get(key))
        return True


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    handler.addFilter(RequestContextFilter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
    # Uvicorn's own handlers otherwise keep emitting plain text.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True


class RequestContextMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers", []))
        try:
            request_id = str(UUID(headers.get(b"x-request-id", b"").decode("ascii")))
        except (ValueError, UnicodeDecodeError):
            request_id = str(uuid4())
        context = {"request_id": request_id, "user_id": None}
        scope.setdefault("state", {})["log_context"] = context
        token = request_context.set(context)

        async def send_with_request_id(message):
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).append(
                    (b"x-request-id", request_id.encode("ascii"))
                )
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            request_context.reset(token)

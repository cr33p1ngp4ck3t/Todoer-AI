from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from ..services.kafka_consumer import KafkaConsumer

router = APIRouter(prefix="/events", tags=["events"])


def setup_event_routes(app):
    """Setup event handling routes"""

    @app.post("/events/task-created")
    async def on_task_created(event_data: Dict[str, Any]):
        """Handle task created event"""
        try:
            await KafkaConsumer.handle_task_created(event_data)
            return {"status": "processed", "event": "task-created"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.post("/events/task-updated")
    async def on_task_updated(event_data: Dict[str, Any]):
        """Handle task updated event"""
        try:
            await KafkaConsumer.handle_task_updated(event_data)
            return {"status": "processed", "event": "task-updated"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.post("/events/task-deleted")
    async def on_task_deleted(event_data: Dict[str, Any]):
        """Handle task deleted event"""
        try:
            await KafkaConsumer.handle_task_deleted(event_data)
            return {"status": "processed", "event": "task-deleted"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.post("/events/task-completed")
    async def on_task_completed(event_data: Dict[str, Any]):
        """Handle task completed event"""
        try:
            await KafkaConsumer.handle_task_completed(event_data)
            return {"status": "processed", "event": "task-completed"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

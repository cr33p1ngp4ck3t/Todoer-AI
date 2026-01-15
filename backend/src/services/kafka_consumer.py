from dapr.ext.fastapi import DaprApp
from fastapi import FastAPI


class KafkaConsumer:
    def __init__(self, app: FastAPI):
        self.dapr_app = DaprApp(app)
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        # Subscribe to task events
        self.dapr_app.subscribe(
            pubsub_name="todo-pubsub",
            topic="task-created",
            route="/events/task-created",
        )
        self.dapr_app.subscribe(
            pubsub_name="todo-pubsub",
            topic="task-updated",
            route="/events/task-updated",
        )
        self.dapr_app.subscribe(
            pubsub_name="todo-pubsub",
            topic="task-deleted",
            route="/events/task-deleted",
        )
        self.dapr_app.subscribe(
            pubsub_name="todo-pubsub",
            topic="task-completed",
            route="/events/task-completed",
        )

    @staticmethod
    async def handle_task_created(event_data: dict):
        """Handle task created event"""
        print(f"Task created event: {event_data}")

    @staticmethod
    async def handle_task_updated(event_data: dict):
        """Handle task updated event"""
        print(f"Task updated event: {event_data}")

    @staticmethod
    async def handle_task_deleted(event_data: dict):
        """Handle task deleted event"""
        print(f"Task deleted event: {event_data}")

    @staticmethod
    async def handle_task_completed(event_data: dict):
        """Handle task completed event"""
        print(f"Task completed event: {event_data}")

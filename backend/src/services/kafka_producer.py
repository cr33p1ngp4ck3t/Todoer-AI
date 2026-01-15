from dapr.clients import DaprClient
from typing import Dict, Any
import json


class KafkaProducer:
    def __init__(self):
        self.dapr = DaprClient()

    async def publish_event(self, topic: str, event: Dict[str, Any]):
        """Publish event to Kafka via Dapr"""
        try:
            await self.dapr.publish_event(
                pubsub_name="todo-pubsub",
                topic_name=topic,
                data=json.dumps(event),
            )
            print(f"Event published to {topic}: {event}")
        except Exception as e:
            print(f"Failed to publish event to {topic}: {e}")
            raise

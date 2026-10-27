import abc
import asyncio
import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set
from shared.config import settings
from shared.logging_setup import get_correlation_id, setup_logger
from shared.models import EventMessage

logger = setup_logger("event_bus")


class BaseEventBus(abc.ABC):
    """Abstract interface for event publishing and subscription."""

    @abc.abstractmethod
    def publish(self, topic: str, data: Dict[str, Any], event_id: Optional[str] = None) -> EventMessage:
        pass

    @abc.abstractmethod
    def subscribe(self, topic: str, handler: Callable[[EventMessage], Any]) -> None:
        pass

    @abc.abstractmethod
    def schedule_delayed(
        self,
        delay_seconds: float,
        topic: str,
        data: Dict[str, Any],
        task_id: Optional[str] = None,
    ) -> None:
        """Schedules an event to be published after delay_seconds (Cloud Tasks equivalent)."""
        pass


class InMemoryEventBus(BaseEventBus):
    """Zero-credentials, in-memory event bus with idempotent deduplication and delayed task timers."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[EventMessage], Any]]] = {}
        self._processed_event_ids: Set[str] = set()
        self._dead_letter_queue: List[Dict[str, Any]] = []
        self._scheduled_timers: Dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def subscribe(self, topic: str, handler: Callable[[EventMessage], Any]) -> None:
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            self._subscribers[topic].append(handler)
            logger.info(f"Registered subscriber for topic '{topic}'")

    def publish(self, topic: str, data: Dict[str, Any], event_id: Optional[str] = None) -> EventMessage:
        if event_id is None:
            import uuid
            event_id = str(uuid.uuid4())

        msg = EventMessage(
            event_id=event_id,
            event_type=topic,
            correlation_id=get_correlation_id(),
            timestamp=datetime.now(timezone.utc),
            data=data,
        )

        with self._lock:
            if event_id in self._processed_event_ids:
                logger.warning(f"Idempotency deduplication: Event {event_id} on {topic} already processed.")
                return msg
            self._processed_event_ids.add(event_id)
            handlers = list(self._subscribers.get(topic, []))

        logger.info(f"Published event '{topic}' (id={event_id}) to {len(handlers)} handlers")

        for handler in handlers:
            try:
                handler(msg)
            except Exception as e:
                logger.error(f"Error handling event {event_id} on topic {topic}: {e}", exc_info=True)
                self._dead_letter_queue.append({
                    "topic": topic,
                    "event": msg.model_dump(),
                    "error": str(e),
                    "failed_at": datetime.now(timezone.utc).isoformat(),
                })

        # Emulate Cloud Run Pub/Sub Push subscriptions via local HTTP webhooks
        try:
            import requests
            _NOTIF = settings.NOTIFICATION_SERVICE_URL
            _EVENT_MAP = {
                "listing.created": (settings.MATCHING_SERVICE_URL, "/events/listing-created"),
                "pickup.completed": (settings.ANALYTICS_SERVICE_URL, "/events/pickup-completed"),
                "match.offered": (_NOTIF, "/events/match-offered"),
                "offer.accepted": (_NOTIF, "/events/offer-accepted"),
                "route.assigned": (_NOTIF, "/events/route-assigned"),
                "listing.expired": (_NOTIF, "/events/listing-expired"),
                "admin.escalation_alert": (_NOTIF, "/events/admin-escalation"),
            }
            if topic in _EVENT_MAP:
                base_url, path = _EVENT_MAP[topic]
                requests.post(f"{base_url}{path}", json=msg.model_dump(mode="json"), timeout=1)
        except Exception:
            pass

        return msg

    def schedule_delayed(
        self,
        delay_seconds: float,
        topic: str,
        data: Dict[str, Any],
        task_id: Optional[str] = None,
    ) -> None:
        """Uses a background threading.Timer to emulate Cloud Tasks delayed escalation."""
        if task_id is None:
            import uuid
            task_id = str(uuid.uuid4())

        def _delayed_dispatch():
            logger.info(f"Delayed task {task_id} fired after {delay_seconds}s for topic {topic}")
            self.publish(topic, data)

        timer = threading.Timer(max(0.1, delay_seconds), _delayed_dispatch)
        timer.daemon = True
        with self._lock:
            self._scheduled_timers[task_id] = timer
        timer.start()
        logger.info(f"Scheduled delayed task {task_id} for topic '{topic}' in {delay_seconds:.1f}s")

    def cancel_scheduled(self, task_id: str) -> bool:
        """Cancel a pending delayed task (e.g. if offer was accepted before timeout)."""
        with self._lock:
            timer = self._scheduled_timers.pop(task_id, None)
            if timer:
                timer.cancel()
                logger.info(f"Cancelled delayed task {task_id}")
                return True
        return False

    def clear(self):
        """Reset internal state (useful for test runs)."""
        with self._lock:
            for timer in self._scheduled_timers.values():
                timer.cancel()
            self._scheduled_timers.clear()
            self._processed_event_ids.clear()
            self._dead_letter_queue.clear()


class PubSubEventBus(BaseEventBus):
    """Google Cloud Pub/Sub event bus supporting Cloud Pub/Sub and local Pub/Sub emulator."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self._handlers: Dict[str, List[Callable[[EventMessage], Any]]] = {}
        self._processed_event_ids: Set[str] = set()

        try:
            from google.cloud import pubsub_v1
            self.publisher = pubsub_v1.PublisherClient()
            self.subscriber = pubsub_v1.SubscriberClient()
            self.enabled = True
        except ImportError:
            logger.warning("google-cloud-pubsub not installed; falling back to in-memory mode")
            self.enabled = False
            self.fallback = InMemoryEventBus()

    def publish(self, topic: str, data: Dict[str, Any], event_id: Optional[str] = None) -> EventMessage:
        if not self.enabled:
            return self.fallback.publish(topic, data, event_id)

        import uuid
        if event_id is None:
            event_id = str(uuid.uuid4())

        msg = EventMessage(
            event_id=event_id,
            event_type=topic,
            correlation_id=get_correlation_id(),
            timestamp=datetime.now(timezone.utc),
            data=data,
        )

        topic_path = self.publisher.topic_path(self.project_id, topic.replace(".", "-"))
        payload_bytes = json.dumps(msg.model_dump(), default=str).encode("utf-8")

        future = self.publisher.publish(
            topic_path,
            data=payload_bytes,
            correlation_id=msg.correlation_id,
            event_id=event_id,
        )
        logger.info(f"Published PubSub message {future.result()} to {topic_path}")
        return msg

    def subscribe(self, topic: str, handler: Callable[[EventMessage], Any]) -> None:
        if not self.enabled:
            return self.fallback.subscribe(topic, handler)

        sub_name = f"{topic.replace('.', '-')}-sub"
        subscription_path = self.subscriber.subscription_path(self.project_id, sub_name)

        def _callback(message):
            try:
                payload = json.loads(message.data.decode("utf-8"))
                msg = EventMessage(**payload)
                if msg.event_id in self._processed_event_ids:
                    message.ack()
                    return
                self._processed_event_ids.add(msg.event_id)
                handler(msg)
                message.ack()
            except Exception as e:
                logger.error(f"Failed to process pubsub message: {e}", exc_info=True)
                message.nack()

        self.subscriber.subscribe(subscription_path, callback=_callback)
        logger.info(f"Subscribed to Pub/Sub subscription {subscription_path}")

    def schedule_delayed(
        self,
        delay_seconds: float,
        topic: str,
        data: Dict[str, Any],
        task_id: Optional[str] = None,
    ) -> None:
        """Delegates delayed task scheduling to Cloud Tasks or local timer fallback."""
        if not self.enabled:
            return self.fallback.schedule_delayed(delay_seconds, topic, data, task_id)

        # Fallback to in-process timer if Cloud Tasks API not configured
        import threading
        def _dispatch():
            self.publish(topic, data)
        timer = threading.Timer(max(0.1, delay_seconds), _dispatch)
        timer.daemon = True
        timer.start()


# Global singleton event bus
_event_bus_instance: Optional[BaseEventBus] = None


def get_event_bus() -> BaseEventBus:
    global _event_bus_instance
    if _event_bus_instance is None:
        bus_type = os.getenv("EVENT_BUS_TYPE", settings.EVENT_BUS_TYPE).lower()
        if bus_type == "pubsub":
            _event_bus_instance = PubSubEventBus(project_id=settings.GCP_PROJECT_ID)
        else:
            _event_bus_instance = InMemoryEventBus()
    return _event_bus_instance

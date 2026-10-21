import os
from typing import Any, Dict, List, Optional
from shared.config import settings
from shared.logging_setup import setup_logger

logger = setup_logger("fcm_notifier")

# In-memory history of dispatched notifications
dispatched_notifications: List[Dict[str, Any]] = []


def send_push_notification(
    token_or_topic: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Sends a push notification via Firebase Cloud Messaging with local mock fallback."""
    fcm_key = os.getenv("FCM_SERVER_KEY") or settings.FCM_SERVER_KEY

    record = {
        "target": token_or_topic,
        "title": title,
        "body": body,
        "data": data or {},
        "status": "delivered_mock",
    }
    dispatched_notifications.append(record)

    if not fcm_key:
        logger.info(f"[MOCK FCM] Dispatched to '{token_or_topic}': {title} - {body}")
        return record

    try:
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=token_or_topic if not token_or_topic.startswith("topic:") else None,
            topic=token_or_topic.replace("topic:", "") if token_or_topic.startswith("topic:") else None,
        )
        response = messaging.send(message)
        logger.info(f"FCM message sent successfully: {response}")
        record["status"] = "sent_fcm"
        record["message_id"] = response
        return record
    except Exception as e:
        logger.warning(f"Failed to send real FCM push ({e}); recorded in mock dispatch buffer", exc_info=True)
        return record

import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from shared.config import settings
from shared.events import EventMessage, get_event_bus
from shared.logging_setup import set_correlation_id, setup_logger
from app.fcm import dispatched_notifications, send_push_notification
from app.sms_provider import MockSmsProvider, get_sms_provider
from app.templates import (
    template_admin_escalation,
    template_listing_expired,
    template_match_offered,
    template_offer_accepted,
    template_route_assigned,
)

logger = setup_logger("notification_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    bus = get_event_bus()
    sms = get_sms_provider()

    def _handle_match_offered(msg: EventMessage):
        tmpl = template_match_offered(msg.data)
        ngo_id = msg.data.get("ngo_id", "all_ngos")
        send_push_notification(f"ngo_{ngo_id}", tmpl["title"], tmpl["body"], data=msg.data)
        sms.send_sms("+919876543211", tmpl["sms"])

    def _handle_offer_accepted(msg: EventMessage):
        tmpl = template_offer_accepted(msg.data)
        donor_id = msg.data.get("donor_id", "all_donors")
        send_push_notification(f"donor_{donor_id}", tmpl["title"], tmpl["body"], data=msg.data)
        sms.send_sms("+919876543210", tmpl["sms"])

    def _handle_route_assigned(msg: EventMessage):
        tmpl = template_route_assigned(msg.data)
        vol_id = msg.data.get("volunteer_id", "all_volunteers")
        send_push_notification(f"vol_{vol_id}", tmpl["title"], tmpl["body"], data=msg.data)
        sms.send_sms("+919876543212", tmpl["sms"])

    def _handle_listing_expired(msg: EventMessage):
        tmpl = template_listing_expired(msg.data)
        donor_id = msg.data.get("donor_id", "all_donors")
        send_push_notification(f"donor_{donor_id}", tmpl["title"], tmpl["body"], data=msg.data)

    def _handle_admin_escalation(msg: EventMessage):
        tmpl = template_admin_escalation(msg.data)
        send_push_notification("topic:admin_alerts", tmpl["title"], tmpl["body"], data=msg.data)
        sms.send_sms("+919876543213", tmpl["sms"])

    bus.subscribe("match.offered", _handle_match_offered)
    bus.subscribe("offer.accepted", _handle_offer_accepted)
    bus.subscribe("route.assigned", _handle_route_assigned)
    bus.subscribe("listing.expired", _handle_listing_expired)
    bus.subscribe("admin.escalation_alert", _handle_admin_escalation)
    logger.info("Notification event listeners registered")
    yield


app = FastAPI(
    title="FoodBridge Notification Service",
    description="Multi-channel notifications (Firebase Cloud Messaging + Pluggable SMS)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    cid = request.headers.get("x-correlation-id") or str(uuid.uuid4())
    set_correlation_id(cid)
    response = await call_next(request)
    response.headers["x-correlation-id"] = cid
    return response


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "notification-service",
        "sms_provider": settings.SMS_PROVIDER,
    }


@app.get("/notifications/history", response_model=List[Dict[str, Any]])
def get_notification_history():
    """Retrieve all dispatched push notifications."""
    return dispatched_notifications


@app.get("/notifications/sms-history", response_model=List[Dict[str, Any]])
def get_sms_history():
    """Retrieve all dispatched SMS records from the provider."""
    provider = get_sms_provider()
    if isinstance(provider, MockSmsProvider):
        return provider.sent_messages
    return []


class ManualNotificationRequest(BaseModel):
    recipient_token: str
    title: str
    body: str


@app.post("/notifications/send")
def manual_send(payload: ManualNotificationRequest):
    return send_push_notification(payload.recipient_token, payload.title, payload.body)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.NOTIFICATION_SERVICE_PORT, reload=True)

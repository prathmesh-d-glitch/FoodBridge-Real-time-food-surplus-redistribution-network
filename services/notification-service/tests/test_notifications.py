import pytest
from shared.events import InMemoryEventBus, get_event_bus
from app.fcm import dispatched_notifications, send_push_notification
from app.main import app
from app.sms_provider import MockSmsProvider, get_sms_provider
from app.templates import template_match_offered, template_offer_accepted


@pytest.fixture(autouse=True)
def reset_notifications():
    dispatched_notifications.clear()
    provider = get_sms_provider()
    if isinstance(provider, MockSmsProvider):
        provider.clear()


def test_template_generation():
    offered_data = {
        "offer_id": "off_123",
        "ngo_name": "Robin Hood Army",
        "rank": 1,
        "score": 0.885,
        "timeout_seconds": 600,
    }
    tmpl = template_match_offered(offered_data)
    assert "10 minutes" in tmpl["body"]
    assert "Robin Hood Army" in tmpl["sms"]

    accepted_data = {
        "listing_id": "list_123",
        "ngo_id": "ngo_indiranagar",
        "portions": 50,
    }
    tmpl_acc = template_offer_accepted(accepted_data)
    assert "50 portions" in tmpl_acc["body"]


def test_mock_sms_dispatch():
    sms = get_sms_provider()
    res = sms.send_sms("+919876543210", "Test SMS verification message")
    assert res["status"] == "delivered_mock"
    assert res["to"] == "+919876543210"

    history = sms.sent_messages
    assert len(history) == 1
    assert history[0]["message"] == "Test SMS verification message"


def test_mock_fcm_dispatch():
    res = send_push_notification("device_token_abc", "Urgent Alert", "50 Portions Available")
    assert res["status"] == "delivered_mock"
    assert len(dispatched_notifications) == 1
    assert dispatched_notifications[0]["title"] == "Urgent Alert"

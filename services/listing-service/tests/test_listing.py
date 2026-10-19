from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from shared.events import InMemoryEventBus, get_event_bus
from shared.firestore_client import get_firestore_client
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    bus = get_event_bus()
    if isinstance(bus, InMemoryEventBus):
        bus.clear()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "listing-service"


def test_create_listing_and_event_emission():
    bus = get_event_bus()
    events_received = []

    def handle_listing_created(msg):
        events_received.append(msg)

    bus.subscribe("listing.created", handle_listing_created)

    payload = {
        "title": "50 Portions Veg Biryani & Raita",
        "description": "Leftover from wedding banquet. Freshly cooked 1 hour ago.",
        "category": "cooked_meals",
        "storage_condition": "hot_hold",
        "dietary_type": "veg",
        "quantity_kg": 18.5,
        "portions": 50,
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "location": {
            "latitude": 12.9716,
            "longitude": 77.5946,
            "address": "Palace Grounds, Bangalore",
        },
    }

    headers = {"Authorization": "Bearer mock-donor-token"}
    response = client.post("/listings", json=payload, headers=headers)
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == payload["title"]
    assert data["status"] == "available"
    assert data["geohash"] is not None
    assert data["safe_until"] is not None

    # Check event was emitted to bus
    assert len(events_received) == 1
    assert events_received[0].event_type == "listing.created"
    assert events_received[0].data["listing_id"] == data["id"]
    assert events_received[0].data["category"] == "cooked_meals"


def test_list_and_get_listings():
    # Fetch all listings
    response = client.get("/listings")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)

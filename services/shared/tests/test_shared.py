from datetime import datetime, timedelta, timezone
import pytest
from shared.auth import verify_firebase_token
from shared.events import InMemoryEventBus
from shared.firestore_client import InMemoryFirestoreClient
from shared.geo import (
    decode_geohash,
    encode_geohash,
    estimate_travel_time_minutes,
    get_geohash_neighbors,
    haversine_distance,
)
from shared.models import (
    FoodCategory,
    GeoPoint,
    StorageCondition,
    UserRole,
)
from shared.spoilage import (
    compute_safe_until,
    get_remaining_shelf_life_minutes,
    is_delivery_feasible,
)


def test_haversine_distance():
    # Bangalore MG Road (12.9716, 77.5946) to Indiranagar (12.9784, 77.6408) ~ 5 km
    dist = haversine_distance(12.9716, 77.5946, 12.9784, 77.6408)
    assert 4.5 < dist < 5.5


def test_geohash_roundtrip():
    lat, lon = 12.971598, 77.594562
    gh = encode_geohash(lat, lon, precision=6)
    assert len(gh) == 6
    dec_lat, dec_lon = decode_geohash(gh)
    assert abs(dec_lat - lat) < 0.05
    assert abs(dec_lon - lon) < 0.05


def test_geohash_neighbors():
    gh = encode_geohash(12.9716, 77.5946, precision=6)
    neighbors = get_geohash_neighbors(gh)
    assert len(neighbors) == 9
    assert gh in neighbors


def test_travel_time_estimation():
    eta = estimate_travel_time_minutes(5.0)  # 5 km in city
    assert eta > 10.0  # At 25 km/h + overhead


def test_spoilage_safe_until():
    now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    # Cooked hot hold = 4 hours
    safe_until = compute_safe_until(FoodCategory.COOKED_MEALS, now, StorageCondition.HOT_HOLD)
    assert safe_until == now + timedelta(hours=4)

    # Chilled cooked = 24 hours
    safe_chilled = compute_safe_until(FoodCategory.COOKED_MEALS, now, StorageCondition.CHILLED)
    assert safe_chilled == now + timedelta(hours=24)


def test_spoilage_feasibility_check():
    now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    safe_until = now + timedelta(minutes=90)  # 90 minutes remaining

    # Trip ETA = 20 mins, handover buffer = 15 mins, safety margin = 30 mins
    # Total required = 20 + 15 = 35 mins; Available window = 90 - 30 = 60 mins -> Feasible!
    feasible, slack, reason = is_delivery_feasible(
        safe_until=safe_until,
        travel_eta_minutes=20.0,
        handover_buffer_minutes=15,
        safety_margin_minutes=30,
        now=now,
    )
    assert feasible is True
    assert slack == 25.0  # 60 - 35 = 25

    # If ETA is 50 mins: total required = 50 + 15 = 65 > 60 -> Infeasible!
    infeasible, slack_neg, reason = is_delivery_feasible(
        safe_until=safe_until,
        travel_eta_minutes=50.0,
        handover_buffer_minutes=15,
        safety_margin_minutes=30,
        now=now,
    )
    assert infeasible is False
    assert slack_neg < 0


def test_in_memory_event_bus_pubsub_and_dedupe():
    bus = InMemoryEventBus()
    received = []

    def handler(msg):
        received.append(msg.data)

    bus.subscribe("test.topic", handler)
    bus.publish("test.topic", {"hello": "world"}, event_id="evt-1")

    # Publish duplicate event id
    bus.publish("test.topic", {"hello": "duplicate"}, event_id="evt-1")

    assert len(received) == 1
    assert received[0]["hello"] == "world"


def test_in_memory_firestore():
    db = InMemoryFirestoreClient()
    db.set_document("listings", "item-1", {"status": "available", "portions": 50})
    db.set_document("listings", "item-2", {"status": "claimed", "portions": 20})

    doc = db.get_document("listings", "item-1")
    assert doc is not None
    assert doc["portions"] == 50

    available = db.query_collection("listings", filters=[("status", "==", "available")])
    assert len(available) == 1
    assert available[0]["status"] == "available"


def test_auth_token_mock():
    user = verify_firebase_token("mock-donor-token")
    assert user.role == UserRole.DONOR
    assert user.uid == "donor_taj_palace"

from datetime import datetime, timedelta, timezone
import pytest
from shared.events import InMemoryEventBus, get_event_bus
from shared.firestore_client import InMemoryFirestoreClient, get_firestore_client
from shared.models import ListingStatus, OfferStatus
from app.main import scan_and_expire_listings


@pytest.fixture(autouse=True)
def clean_state():
    db = get_firestore_client()
    bus = get_event_bus()
    if isinstance(db, InMemoryFirestoreClient):
        db.clear()
    if isinstance(bus, InMemoryEventBus):
        bus.clear()


def test_scan_and_expire_listings():
    db = get_firestore_client()
    bus = get_event_bus()
    now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)

    # 1. Expired listing (safe_until was 10 mins ago)
    db.set_document(
        "listings",
        "list_old",
        {
            "id": "list_old",
            "donor_id": "donor_1",
            "donor_name": "Hotel Royal",
            "title": "Expired Biryani",
            "category": "cooked_meals",
            "storage_condition": "ambient",
            "dietary_type": "veg",
            "quantity_kg": 10.0,
            "portions": 25,
            "prepared_at": (now - timedelta(hours=4)).isoformat(),
            "safe_until": (now - timedelta(minutes=10)).isoformat(),
            "location": {"latitude": 12.9716, "longitude": 77.5946},
            "geohash": "tdr1vw",
            "status": ListingStatus.AVAILABLE.value,
        },
    )

    # 2. Fresh listing (safe_until is 2 hours from now)
    db.set_document(
        "listings",
        "list_fresh",
        {
            "id": "list_fresh",
            "donor_id": "donor_1",
            "donor_name": "Hotel Royal",
            "title": "Fresh Bread",
            "category": "bakery_bread",
            "storage_condition": "ambient",
            "dietary_type": "veg",
            "quantity_kg": 5.0,
            "portions": 20,
            "prepared_at": now.isoformat(),
            "safe_until": (now + timedelta(hours=2)).isoformat(),
            "location": {"latitude": 12.9716, "longitude": 77.5946},
            "geohash": "tdr1vw",
            "status": ListingStatus.AVAILABLE.value,
        },
    )

    # Pending offer on old listing
    db.set_document(
        "offers",
        "off_old",
        {
            "id": "off_old",
            "listing_id": "list_old",
            "ngo_id": "ngo_1",
            "status": OfferStatus.OFFERED.value,
        },
    )

    expired_events = []
    bus.subscribe("listing.expired", lambda msg: expired_events.append(msg))

    expired_ids = scan_and_expire_listings(now=now)

    assert "list_old" in expired_ids
    assert "list_fresh" not in expired_ids

    # Old listing status updated to expired
    old_doc = db.get_document("listings", "list_old")
    assert old_doc["status"] == ListingStatus.EXPIRED.value

    # Fresh listing remains available
    fresh_doc = db.get_document("listings", "list_fresh")
    assert fresh_doc["status"] == ListingStatus.AVAILABLE.value

    # Pending offer on old listing cancelled
    off_doc = db.get_document("offers", "off_old")
    assert off_doc["status"] == OfferStatus.CANCELLED.value

    # Event emitted
    assert len(expired_events) == 1
    assert expired_events[0].data["listing_id"] == "list_old"

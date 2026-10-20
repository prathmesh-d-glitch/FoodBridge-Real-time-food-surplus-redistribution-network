from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from shared.events import get_event_bus
from shared.firestore_client import get_firestore_client
from shared.models import (
    DietaryType,
    GeoPoint,
    OfferStatus,
    UserProfile,
    UserRole,
    VerificationStatus,
)
import pytest
from app.cascade import CascadeManager
from app.main import app as matching_app
from shared.firestore_client import InMemoryFirestoreClient


@pytest.fixture(autouse=True)
def clean_db():
    db = get_firestore_client()
    if isinstance(db, InMemoryFirestoreClient):
        db.clear()


def test_full_listing_to_offer_flow():
    """Verifies that listing.created event reliably triggers matching-service to generate rank 1 offer."""
    db = get_firestore_client()
    bus = get_event_bus()

    # Seed an NGO
    ngo = UserProfile(
        uid="ngo_indiranagar",
        email="ind@ngo.org",
        name="Indiranagar Shelter",
        role=UserRole.NGO,
        location=GeoPoint(latitude=12.9784, longitude=77.6408),
        capacity_kg=200.0,
        dietary_preferences=[DietaryType.ANY],
        reliability_score=0.96,
        verification_status=VerificationStatus.VERIFIED,
    )
    db.set_document("users", ngo.uid, ngo.model_dump(mode="json"))

    # Seed a listing created in DB
    now = datetime.now(timezone.utc)
    listing_id = "list_integration_test_1"
    listing_data = {
        "id": listing_id,
        "donor_id": "donor_taj_palace",
        "donor_name": "Taj Palace",
        "title": "Fresh Paneer Curry & Naan",
        "description": "Buffet surplus",
        "category": "cooked_meals",
        "storage_condition": "hot_hold",
        "dietary_type": "veg",
        "quantity_kg": 30.0,
        "portions": 80,
        "prepared_at": now.isoformat(),
        "safe_until": (now + timedelta(hours=3)).isoformat(),
        "location": {"latitude": 12.9716, "longitude": 77.5946},
        "geohash": "tdr1vw",
        "status": "available",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    db.set_document("listings", listing_id, listing_data)

    # Trigger via matching-service push event endpoint
    client = TestClient(matching_app)
    response = client.post(
        "/events/listing-created",
        json={"listing_id": listing_id},
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "processed"
    assert res_data["offer_created"] is True
    assert res_data["offer_id"] is not None

    # Verify offer exists in offers collection
    offer = db.get_document("offers", res_data["offer_id"])
    assert offer is not None
    assert offer["ngo_id"] == "ngo_indiranagar"
    assert offer["rank"] == 1
    assert offer["status"] == OfferStatus.OFFERED.value

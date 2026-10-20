from datetime import datetime, timedelta, timezone
import pytest
from shared.events import InMemoryEventBus, get_event_bus
from shared.firestore_client import InMemoryFirestoreClient, get_firestore_client
from shared.models import (
    DietaryType,
    DonorListing,
    FoodCategory,
    GeoPoint,
    ListingStatus,
    OfferStatus,
    StorageCondition,
    UserProfile,
    UserRole,
    VerificationStatus,
)
from app.cascade import CascadeManager


@pytest.fixture(autouse=True)
def setup_test_environment():
    db = get_firestore_client()
    bus = get_event_bus()
    if isinstance(db, InMemoryFirestoreClient):
        db.clear()
    if isinstance(bus, InMemoryEventBus):
        bus.clear()

    # Seed 3 verified NGOs in Bangalore
    ngos = [
        UserProfile(
            uid="ngo_indiranagar",
            email="ind@ngo.org",
            name="Indiranagar Food Rescue",
            role=UserRole.NGO,
            location=GeoPoint(latitude=12.9784, longitude=77.6408),  # ~5km from MG road
            capacity_kg=150.0,
            dietary_preferences=[DietaryType.ANY],
            reliability_score=0.98,
            verification_status=VerificationStatus.VERIFIED,
        ),
        UserProfile(
            uid="ngo_koramangala",
            email="kora@ngo.org",
            name="Koramangala Community Kitchen",
            role=UserRole.NGO,
            location=GeoPoint(latitude=12.9352, longitude=77.6245),  # ~6.5km from MG road
            capacity_kg=100.0,
            dietary_preferences=[DietaryType.ANY],
            reliability_score=0.92,
            verification_status=VerificationStatus.VERIFIED,
        ),
        UserProfile(
            uid="ngo_whitefield",
            email="wf@ngo.org",
            name="Whitefield Shelter",
            role=UserRole.NGO,
            location=GeoPoint(latitude=12.9698, longitude=77.7499),  # ~17km from MG road
            capacity_kg=200.0,
            dietary_preferences=[DietaryType.ANY],
            reliability_score=0.88,
            verification_status=VerificationStatus.VERIFIED,
        ),
    ]

    for ngo in ngos:
        db.set_document("users", ngo.uid, ngo.model_dump(mode="json"))


def test_timeout_clamping():
    manager = CascadeManager()
    now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)

    # 1. 50 minutes remaining: 50 * 0.10 = 5 minutes -> 300 seconds
    t1 = manager.compute_response_timeout_seconds(now + timedelta(minutes=50), now=now)
    assert t1 == 300

    # 2. 200 minutes remaining: 200 * 0.10 = 20 minutes -> clamped to max 15 minutes = 900 seconds
    t2 = manager.compute_response_timeout_seconds(now + timedelta(minutes=200), now=now)
    assert t2 == 900

    # 3. 10 minutes remaining: 10 * 0.10 = 1 minute -> clamped to min 3 minutes = 180 seconds
    t3 = manager.compute_response_timeout_seconds(now + timedelta(minutes=10), now=now)
    assert t3 == 180


def test_initial_offer_to_rank_1():
    db = get_firestore_client()
    bus = get_event_bus()
    manager = CascadeManager()

    now = datetime.now(timezone.utc)
    listing = DonorListing(
        id="list_test_101",
        donor_id="donor_caterer_1",
        donor_name="Royal Palace",
        title="100 Meals Paneer Rice",
        category=FoodCategory.COOKED_MEALS,
        storage_condition=StorageCondition.HOT_HOLD,
        dietary_type=DietaryType.VEG,
        quantity_kg=25.0,
        portions=100,
        prepared_at=now,
        safe_until=now + timedelta(hours=3),
        location=GeoPoint(latitude=12.9716, longitude=77.5946),
        geohash="tdr1vw",
        status=ListingStatus.AVAILABLE,
    )
    db.set_document("listings", listing.id, listing.model_dump(mode="json"))

    events = []
    bus.subscribe("match.offered", lambda msg: events.append(msg))

    offer = manager.process_new_listing(listing.id)
    assert offer is not None
    assert offer.rank == 1
    # Rank 1 should be Indiranagar (closest with high reliability)
    assert offer.ngo_id == "ngo_indiranagar"
    assert offer.status == OfferStatus.OFFERED
    assert len(events) == 1
    assert events[0].data["offer_id"] == offer.id


def test_cascade_escalation_on_decline():
    db = get_firestore_client()
    bus = get_event_bus()
    manager = CascadeManager()

    now = datetime.now(timezone.utc)
    listing = DonorListing(
        id="list_test_102",
        donor_id="donor_caterer_1",
        donor_name="Royal Palace",
        title="Surplus Rotis",
        category=FoodCategory.BAKERY_BREAD,
        storage_condition=StorageCondition.AMBIENT,
        dietary_type=DietaryType.VEG,
        quantity_kg=15.0,
        portions=50,
        prepared_at=now,
        safe_until=now + timedelta(hours=12),
        location=GeoPoint(latitude=12.9716, longitude=77.5946),
        geohash="tdr1vw",
        status=ListingStatus.AVAILABLE,
    )
    db.set_document("listings", listing.id, listing.model_dump(mode="json"))

    # Initial offer to rank 1
    offer1 = manager.process_new_listing(listing.id)
    assert offer1.rank == 1
    assert offer1.ngo_id == "ngo_indiranagar"

    declined_events = []
    offered_events = []
    bus.subscribe("offer.declined", lambda msg: declined_events.append(msg))
    bus.subscribe("match.offered", lambda msg: offered_events.append(msg))

    # NGO 1 declines
    manager.decline_offer(offer1.id, ngo_id=offer1.ngo_id, reason="Volunteers busy")

    # Check offer 1 is marked declined
    updated_offer1 = db.get_document("offers", offer1.id)
    assert updated_offer1["status"] == OfferStatus.DECLINED.value

    # Auto-escalation should have offered to rank 2!
    offers = db.query_collection("offers", filters=[("listing_id", "==", listing.id)])
    assert len(offers) == 2
    offer2 = [o for o in offers if o["rank"] == 2][0]
    assert offer2["status"] == OfferStatus.OFFERED.value
    assert offer2["ngo_id"] == "ngo_koramangala"  # Rank 2 candidate


def test_offer_acceptance_and_conflict_cancellation():
    db = get_firestore_client()
    bus = get_event_bus()
    manager = CascadeManager()

    now = datetime.now(timezone.utc)
    listing = DonorListing(
        id="list_test_103",
        donor_id="donor_caterer_1",
        donor_name="Royal Palace",
        title="50 Portions Veg Pulao",
        category=FoodCategory.COOKED_MEALS,
        storage_condition=StorageCondition.HOT_HOLD,
        dietary_type=DietaryType.VEG,
        quantity_kg=15.0,
        portions=50,
        prepared_at=now,
        safe_until=now + timedelta(hours=3),
        location=GeoPoint(latitude=12.9716, longitude=77.5946),
        geohash="tdr1vw",
        status=ListingStatus.AVAILABLE,
    )
    db.set_document("listings", listing.id, listing.model_dump(mode="json"))

    accepted_events = []
    bus.subscribe("offer.accepted", lambda msg: accepted_events.append(msg))

    offer = manager.process_new_listing(listing.id)
    accepted_offer, updated_listing = manager.accept_offer(offer.id, ngo_id=offer.ngo_id)

    assert accepted_offer.status == OfferStatus.ACCEPTED
    assert updated_listing.status == ListingStatus.CLAIMED
    assert updated_listing.claimed_by_ngo_id == offer.ngo_id
    assert len(accepted_events) == 1
    assert accepted_events[0].data["offer_id"] == offer.id

from datetime import datetime, timedelta, timezone
from shared.models import (
    DietaryType,
    DonorListing,
    FoodCategory,
    GeoPoint,
    ListingStatus,
    StorageCondition,
    UserProfile,
    UserRole,
    VerificationStatus,
)
from app.scoring import calculate_match_score


def create_test_listing(
    prepared_hours_ago: float = 0.5,
    safe_hours_total: float = 4.0,
    dietary: DietaryType = DietaryType.VEG,
    quantity_kg: float = 20.0,
) -> DonorListing:
    now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    prepared_at = now - timedelta(hours=prepared_hours_ago)
    safe_until = prepared_at + timedelta(hours=safe_hours_total)

    return DonorListing(
        id="list_biryani_1",
        donor_id="donor_caterer_1",
        donor_name="Grand Banquet Hall",
        title="Biryani & Salan",
        category=FoodCategory.COOKED_MEALS,
        storage_condition=StorageCondition.HOT_HOLD,
        dietary_type=dietary,
        quantity_kg=quantity_kg,
        portions=60,
        prepared_at=prepared_at,
        safe_until=safe_until,
        location=GeoPoint(latitude=12.9716, longitude=77.5946),  # MG Road, Bangalore
        geohash="tdr1vw",
        status=ListingStatus.AVAILABLE,
    )


def create_test_ngo(
    uid: str = "ngo_1",
    name: str = "Robin Hood Army",
    lat: float = 12.9784,
    lon: float = 77.6408,  # ~5 km away
    dietary_preferences: list = None,
    capacity_kg: float = 100.0,
    reliability_score: float = 0.95,
) -> UserProfile:
    return UserProfile(
        uid=uid,
        email="test@ngo.org",
        name=name,
        role=UserRole.NGO,
        location=GeoPoint(latitude=lat, longitude=lon),
        capacity_kg=capacity_kg,
        dietary_preferences=dietary_preferences or [DietaryType.ANY],
        reliability_score=reliability_score,
        verification_status=VerificationStatus.VERIFIED,
    )


def test_scoring_weights_and_breakdown():
    now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    listing = create_test_listing(prepared_hours_ago=0.5, safe_hours_total=4.0)
    ngo = create_test_ngo()

    score, breakdown, eligible, reason = calculate_match_score(listing, ngo, now=now)
    assert eligible is True
    assert breakdown is not None
    assert 0.0 < score <= 1.0

    # Verify explainability fields
    assert breakdown.time_feasibility > 0.0
    assert breakdown.proximity > 0.0
    assert breakdown.capacity_fit > 0.0
    assert breakdown.dietary_match == 1.0
    assert breakdown.reliability == 0.95
    assert breakdown.need_urgency > 0.0

    # Verify formula breakdown sum
    expected_score = round(
        0.30 * breakdown.time_feasibility
        + 0.25 * breakdown.proximity
        + 0.15 * breakdown.capacity_fit
        + 0.10 * breakdown.dietary_match
        + 0.15 * breakdown.reliability
        + 0.05 * breakdown.need_urgency,
        4,
    )
    assert abs(score - expected_score) < 0.001


def test_spoilage_hard_filter_rejection():
    now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    # Listing was prepared 3.8 hours ago, safe shelf life is 4 hours -> only 12 minutes remaining!
    listing = create_test_listing(prepared_hours_ago=3.8, safe_hours_total=4.0)
    ngo = create_test_ngo()

    score, breakdown, eligible, reason = calculate_match_score(listing, ngo, now=now)
    # Hard filter must fail because remaining shelf life (12 mins) < safety margin (30 mins)
    assert eligible is False
    assert score == 0.0
    assert "Spoilage filter failed" in reason


def test_dietary_incompatibility_rejection():
    now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    # Non-veg listing
    listing = create_test_listing(dietary=DietaryType.NON_VEG)
    # Strictly Jain NGO
    ngo = create_test_ngo(dietary_preferences=[DietaryType.JAIN])

    score, breakdown, eligible, reason = calculate_match_score(listing, ngo, now=now)
    assert eligible is False
    assert score == 0.0
    assert "Dietary incompatibility" in reason


def test_proximity_ranking():
    now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    listing = create_test_listing()

    # NGO 1 is 2 km away
    ngo_near = create_test_ngo("ngo_near", lat=12.9800, lon=77.6000)
    # NGO 2 is 18 km away
    ngo_far = create_test_ngo("ngo_far", lat=13.1000, lon=77.6500)

    score_near, bd_near, _, _ = calculate_match_score(listing, ngo_near, now=now)
    score_far, bd_far, _, _ = calculate_match_score(listing, ngo_far, now=now)

    assert score_near > score_far
    assert bd_near.proximity > bd_far.proximity

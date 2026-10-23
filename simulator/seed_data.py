import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "services" / "shared"))

from shared.firestore_client import get_firestore_client
from shared.models import (
    DietaryType,
    FoodCategory,
    GeoPoint,
    ListingStatus,
    StorageCondition,
    UserProfile,
    UserRole,
    VerificationStatus,
)


def seed_database():
    """Seeds verified NGOs, donors, volunteers, active listings, and baseline impact records."""
    db = get_firestore_client()
    now = datetime.now(timezone.utc)

    # 1. Verified NGOs across Bangalore
    ngos = [
        UserProfile(
            uid="ngo_robin_hood",
            email="ops@robinhoodarmy.example",
            name="Robin Hood Army Bangalore",
            role=UserRole.NGO,
            phone="+919876543211",
            location=GeoPoint(latitude=12.9784, longitude=77.6408, address="100 Feet Road, Indiranagar"),
            capacity_kg=250.0,
            dietary_preferences=[DietaryType.ANY],
            reliability_score=0.98,
            verification_status=VerificationStatus.VERIFIED,
        ),
        UserProfile(
            uid="ngo_koramangala",
            email="kitchen@kora.example",
            name="Koramangala Community Kitchen",
            role=UserRole.NGO,
            phone="+919876543214",
            location=GeoPoint(latitude=12.9352, longitude=77.6245, address="80 Feet Road, Koramangala 4th Block"),
            capacity_kg=150.0,
            dietary_preferences=[DietaryType.VEG],
            reliability_score=0.93,
            verification_status=VerificationStatus.VERIFIED,
        ),
        UserProfile(
            uid="ngo_hasiru_dala",
            email="help@hasirudala.example",
            name="Hasiru Dala Feeding Centre",
            role=UserRole.NGO,
            phone="+919876543215",
            location=GeoPoint(latitude=12.9634, longitude=77.5855, address="KR Market Shelter"),
            capacity_kg=300.0,
            dietary_preferences=[DietaryType.ANY],
            reliability_score=0.95,
            verification_status=VerificationStatus.VERIFIED,
        ),
    ]

    for ngo in ngos:
        db.set_document("users", ngo.uid, ngo.model_dump(mode="json"))

    # 2. Donors
    donors = [
        UserProfile(
            uid="donor_taj_palace",
            email="chef@tajpalace.example",
            name="Taj Palace Luxury Catering",
            role=UserRole.DONOR,
            phone="+919876543210",
            location=GeoPoint(latitude=12.9716, longitude=77.5946, address="MG Road, Bangalore"),
            verification_status=VerificationStatus.VERIFIED,
        ),
        UserProfile(
            uid="donor_grand_banquet",
            email="manager@grandbanquet.example",
            name="Grand Convention & Banquets",
            role=UserRole.DONOR,
            phone="+919876543216",
            location=GeoPoint(latitude=13.0033, longitude=77.5891, address="Palace Grounds Gate 4"),
            verification_status=VerificationStatus.VERIFIED,
        ),
    ]

    for donor in donors:
        db.set_document("users", donor.uid, donor.model_dump(mode="json"))

    # 3. Volunteers
    volunteers = [
        UserProfile(
            uid="vol_arun_kumar",
            email="arun.k@volunteer.example",
            name="Arun Kumar",
            role=UserRole.VOLUNTEER,
            phone="+919876543212",
            location=GeoPoint(latitude=12.9700, longitude=77.5900, address="Cubbon Park Area"),
            verification_status=VerificationStatus.VERIFIED,
        ),
    ]

    for vol in volunteers:
        db.set_document("users", vol.uid, vol.model_dump(mode="json"))

    # 4. Active surplus listings with Freshness Clocks and Gemini hints
    listings = [
        {
            "id": "list_wedding_rush_1",
            "donor_id": "donor_taj_palace",
            "donor_name": "Taj Palace Luxury Catering",
            "title": "Wedding Feast: Vegetable Dum Biryani & Mirchi Salan",
            "description": "Leftover luncheon banquet from wedding reception. Kept in hot holding containers at 68°C.",
            "category": FoodCategory.COOKED_MEALS.value,
            "storage_condition": StorageCondition.HOT_HOLD.value,
            "dietary_type": DietaryType.VEG.value,
            "quantity_kg": 42.0,
            "portions": 120,
            "prepared_at": (now - timedelta(minutes=45)).isoformat(),
            "safe_until": (now + timedelta(hours=3, minutes=15)).isoformat(),
            "location": {"latitude": 12.9716, "longitude": 77.5946, "address": "MG Road, Bangalore"},
            "geohash": "tdr1vw",
            "photo_analysis": {
                "food_type": "Cooked Catering Meals (Rice & Gravy)",
                "estimated_portions": 120,
                "shelf_life_hours_hint": 4.0,
                "safety_flags": ["Hot holding verified above 65°C", "Food-grade stainless steel containers"],
                "confidence": 0.95,
                "source": "gemini",
            },
            "status": ListingStatus.AVAILABLE.value,
            "created_at": (now - timedelta(minutes=45)).isoformat(),
            "updated_at": (now - timedelta(minutes=45)).isoformat(),
        },
        {
            "id": "list_bakery_fresh",
            "donor_id": "donor_grand_banquet",
            "donor_name": "Grand Convention & Banquets",
            "title": "Fresh Artisan Breads, Dinner Rolls & Croissants",
            "description": "Morning breakfast buffet surplus, sealed dry ambient packaging.",
            "category": FoodCategory.BAKERY_BREAD.value,
            "storage_condition": StorageCondition.AMBIENT.value,
            "dietary_type": DietaryType.VEG.value,
            "quantity_kg": 18.0,
            "portions": 55,
            "prepared_at": (now - timedelta(hours=2)).isoformat(),
            "safe_until": (now + timedelta(hours=22)).isoformat(),
            "location": {"latitude": 13.0033, "longitude": 77.5891, "address": "Palace Grounds Gate 4"},
            "geohash": "tdr1w2",
            "photo_analysis": {
                "food_type": "Bakery & Breads",
                "estimated_portions": 55,
                "shelf_life_hours_hint": 24.0,
                "safety_flags": ["Sealed ambient storage", "Zero moisture condensation"],
                "confidence": 0.92,
                "source": "gemini",
            },
            "status": ListingStatus.AVAILABLE.value,
            "created_at": (now - timedelta(hours=2)).isoformat(),
            "updated_at": (now - timedelta(hours=2)).isoformat(),
        },
    ]

    for l in listings:
        db.set_document("listings", l["id"], l)

    # 5. Baseline impact records
    from services.analytics_service.app.impact import ImpactCalculator
    import importlib.util
    spec = importlib.util.spec_from_file_location("impact_calc", root_dir / "services" / "analytics-service" / "app" / "impact.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    calc = mod.ImpactCalculator()
    calc.record_completed_pickup("list_prev_01", "donor_taj_palace", "ngo_robin_hood", 65.0, 180)
    calc.record_completed_pickup("list_prev_02", "donor_grand_banquet", "ngo_koramangala", 45.0, 125)

    print("Successfully seeded FoodBridge database with realistic entities!")


if __name__ == "__main__":
    seed_database()

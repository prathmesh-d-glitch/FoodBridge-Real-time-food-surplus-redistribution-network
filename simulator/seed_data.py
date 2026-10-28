import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(root_dir / "services" / "shared") not in sys.path:
    sys.path.insert(0, str(root_dir / "services" / "shared"))

from shared.firestore_client import get_firestore_client
from shared.models import (
    DietaryType,
    FoodCategory,
    GeoPoint,
    ListingStatus,
    OfferStatus,
    RouteStatus,
    StorageCondition,
    UserProfile,
    UserRole,
    VerificationStatus,
)


def seed_database():
    db = get_firestore_client()
    now = datetime.now(timezone.utc)

    # 1. Donors
    donors = [
        UserProfile(
            uid="donor_taj_palace",
            email="donor@gmail.com",
            name="Taj Palace Luxury Catering",
            role=UserRole.DONOR,
            phone="+919876543210",
            location=GeoPoint(latitude=12.9716, longitude=77.5946, address="MG Road, Bangalore"),
            verification_status=VerificationStatus.VERIFIED,
            fssai_license="11223344556677",
        ),
        UserProfile(
            uid="donor_grand_banquet",
            email="banquets@grandconvention.example",
            name="Grand Convention & Banquets",
            role=UserRole.DONOR,
            phone="+919876543214",
            location=GeoPoint(latitude=13.0033, longitude=77.5891, address="Palace Grounds Gate 4"),
            verification_status=VerificationStatus.VERIFIED,
            fssai_license="11229988776655",
        ),
        UserProfile(
            uid="donor_gwalior_palace",
            email="gwalior.palace.donor@gmail.com",
            name="Gwalior Heritage Palace Catering",
            role=UserRole.DONOR,
            phone="+919876577005",
            location=GeoPoint(latitude=26.2045, longitude=78.1560, address="Jayaji Chowk, Lashkar, Gwalior, MP"),
            verification_status=VerificationStatus.VERIFIED,
            fssai_license="10423001000542",
        ),
        UserProfile(
            uid="donor_gwalior_banquets",
            email="gwalior.banquets.donor@gmail.com",
            name="Gwalior Central Banquets & Sweets",
            role=UserRole.DONOR,
            phone="+919876577006",
            location=GeoPoint(latitude=26.2198, longitude=78.1820, address="Station Road, Padav, Gwalior, MP"),
            verification_status=VerificationStatus.VERIFIED,
            fssai_license="10423001000889",
        ),
    ]

    for d in donors:
        db.set_document("users", d.uid, d.model_dump(mode="json"))

    # 2. NGOs
    ngos = [
        UserProfile(
            uid="ngo_robin_hood",
            email="ngo@gmail.com",
            name="Robin Hood Army Bangalore",
            role=UserRole.NGO,
            phone="+919876543211",
            location=GeoPoint(latitude=12.9784, longitude=77.6408, address="100ft Rd, Indiranagar"),
            verification_status=VerificationStatus.VERIFIED,
            capacity_kg=250.0,
            dietary_preferences=[DietaryType.VEG, DietaryType.NON_VEG],
            reliability_score=0.96,
        ),
        UserProfile(
            uid="ngo_koramangala",
            email="kitchen@koramangala.org",
            name="Koramangala Community Kitchen",
            role=UserRole.NGO,
            phone="+919876543215",
            location=GeoPoint(latitude=12.9352, longitude=77.6245, address="80ft Rd, Koramangala"),
            verification_status=VerificationStatus.VERIFIED,
            capacity_kg=150.0,
            dietary_preferences=[DietaryType.VEG],
            reliability_score=0.91,
        ),
        UserProfile(
            uid="ngo_gwalior_annapurna",
            email="gwalior.annapurna.ngo@gmail.com",
            name="Gwalior Annapurna Food Bank",
            role=UserRole.NGO,
            phone="+919876577002",
            location=GeoPoint(latitude=26.2124, longitude=78.1772, address="Patel Nagar, City Center, Gwalior, MP"),
            verification_status=VerificationStatus.VERIFIED,
            capacity_kg=300.0,
            dietary_preferences=[DietaryType.VEG],
            reliability_score=0.97,
        ),
        UserProfile(
            uid="ngo_gwalior_relief",
            email="gwalior.relief.ngo@gmail.com",
            name="Gwalior Robin Hood Relief",
            role=UserRole.NGO,
            phone="+919876577003",
            location=GeoPoint(latitude=26.2289, longitude=78.2254, address="Mall Road, Morar Cantt, Gwalior, MP"),
            verification_status=VerificationStatus.VERIFIED,
            capacity_kg=220.0,
            dietary_preferences=[DietaryType.VEG, DietaryType.NON_VEG],
            reliability_score=0.94,
        ),
    ]

    for ngo in ngos:
        db.set_document("users", ngo.uid, ngo.model_dump(mode="json"))

    # 3. Volunteers & Admins
    volunteers = [
        UserProfile(
            uid="vol_arun_kumar",
            email="volunteer@gmail.com",
            name="Arun Kumar",
            role=UserRole.VOLUNTEER,
            phone="+919876543212",
            location=GeoPoint(latitude=12.9700, longitude=77.5900, address="Cubbon Park Area"),
            verification_status=VerificationStatus.VERIFIED,
        ),
        UserProfile(
            uid="vol_gwalior_vikram",
            email="gwalior.volunteer@gmail.com",
            name="Gwalior Rapid Courier Vikram",
            role=UserRole.VOLUNTEER,
            phone="+919876577004",
            location=GeoPoint(latitude=26.2167, longitude=78.1695, address="Phoolbagh Chowk, Lashkar, Gwalior, MP"),
            verification_status=VerificationStatus.VERIFIED,
        ),
        UserProfile(
            uid="admin_gwalior",
            email="gwalior.admin@gmail.com",
            name="FoodBridge Gwalior Regional Admin",
            role=UserRole.ADMIN,
            phone="+919876577001",
            location=GeoPoint(latitude=26.2235, longitude=78.1792, address="Collectorate Road, City Center, Gwalior, MP"),
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
            "location": {"latitude": 12.9716, "longitude": 77.5946, "address": "Palace Grounds, MG Road, Bangalore"},
            "geohash": "tdr1vw",
            "photo_analysis": {
                "food_type": "Cooked Catering Meals (Rice & Gravy)",
                "estimated_portions": 120,
                "shelf_life_hours_hint": 4.0,
                "safety_flags": ["Hot holding verified above 65°C", "Food-grade stainless steel containers"],
                "confidence": 0.95,
                "source": "gemini",
            },
            "status": ListingStatus.OFFERED.value,
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
            "location": {"latitude": 13.0033, "longitude": 77.5891, "address": "Palace Grounds Gate 4, Bengaluru"},
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
        {
            "id": "list_gwalior_wedding_feast",
            "donor_id": "donor_gwalior_palace",
            "donor_name": "Gwalior Heritage Palace Catering",
            "title": "Gwalior Royal Feast: Shahi Paneer, Dal Makhani & Jeera Rice",
            "description": "Grand wedding banquet surplus from Lashkar Gwalior. Maintained in insulated hot holding vessels at 67°C.",
            "category": FoodCategory.COOKED_MEALS.value,
            "storage_condition": StorageCondition.HOT_HOLD.value,
            "dietary_type": DietaryType.VEG.value,
            "quantity_kg": 45.0,
            "portions": 130,
            "prepared_at": (now - timedelta(minutes=30)).isoformat(),
            "safe_until": (now + timedelta(hours=3, minutes=30)).isoformat(),
            "location": {"latitude": 26.2045, "longitude": 78.1560, "address": "Jayaji Chowk, Lashkar, Gwalior, Madhya Pradesh"},
            "geohash": "tu345x",
            "photo_analysis": {
                "food_type": "Royal Catering Feast",
                "estimated_portions": 130,
                "shelf_life_hours_hint": 4.0,
                "safety_flags": ["Hot-hold 67°C verified", "Stainless steel containers"],
                "confidence": 0.96,
                "source": "gemini",
            },
            "status": ListingStatus.OFFERED.value,
            "created_at": (now - timedelta(minutes=30)).isoformat(),
            "updated_at": (now - timedelta(minutes=30)).isoformat(),
        },
        {
            "id": "list_gwalior_sweets_buffet",
            "donor_id": "donor_gwalior_banquets",
            "donor_name": "Gwalior Central Banquets & Sweets",
            "title": "Gwalior Delicacies: Morena Gajak, Besan Ladoo & Peda Boxes",
            "description": "Banquet dessert surplus packed in food-grade sealed cartons at Padav Station Road Gwalior.",
            "category": FoodCategory.DESSERTS.value,
            "storage_condition": StorageCondition.AMBIENT.value,
            "dietary_type": DietaryType.VEG.value,
            "quantity_kg": 22.0,
            "portions": 70,
            "prepared_at": (now - timedelta(hours=1)).isoformat(),
            "safe_until": (now + timedelta(hours=23)).isoformat(),
            "location": {"latitude": 26.2198, "longitude": 78.1820, "address": "Station Road, Padav, Gwalior, Madhya Pradesh"},
            "geohash": "tu347s",
            "photo_analysis": {
                "food_type": "Traditional Confectionery & Sweets",
                "estimated_portions": 70,
                "shelf_life_hours_hint": 24.0,
                "safety_flags": ["Ambient dry storage", "Sealed packaging"],
                "confidence": 0.94,
                "source": "gemini",
            },
            "status": ListingStatus.AVAILABLE.value,
            "created_at": (now - timedelta(hours=1)).isoformat(),
            "updated_at": (now - timedelta(hours=1)).isoformat(),
        },
    ]

    for l in listings:
        db.set_document("listings", l["id"], l)

    # 5. Active offer for ngo_robin_hood (ngo@gmail.com)
    active_offer = {
        "id": "off_seed_robin_hood_01",
        "listing_id": "list_wedding_rush_1",
        "donor_id": "donor_taj_palace",
        "ngo_id": "ngo_robin_hood",
        "ngo_name": "Robin Hood Army Bangalore",
        "rank": 1,
        "score": 0.91,
        "score_breakdown": {
            "time_feasibility": 0.95,
            "proximity": 0.88,
            "capacity_fit": 0.92,
            "dietary_match": 1.0,
            "reliability": 0.96,
            "need_urgency": 0.85,
            "total_score": 0.91,
            "explanation": "High capacity fit (120 portions) within 4.5km radius and 2h45m safety margin.",
        },
        "status": OfferStatus.OFFERED.value,
        "response_timeout_seconds": 600,
        "offered_at": (now - timedelta(minutes=5)).isoformat(),
        "expires_at": (now + timedelta(minutes=9, seconds=30)).isoformat(),
    }
    db.set_document("offers", active_offer["id"], active_offer)

    # 5b. Active offer for ngo_gwalior_annapurna (gwalior.annapurna.ngo@gmail.com)
    active_offer_gwl = {
        "id": "off_seed_gwalior_01",
        "listing_id": "list_gwalior_wedding_feast",
        "donor_id": "donor_gwalior_palace",
        "ngo_id": "ngo_gwalior_annapurna",
        "ngo_name": "Gwalior Annapurna Food Bank",
        "rank": 1,
        "score": 0.95,
        "score_breakdown": {
            "time_feasibility": 0.98,
            "proximity": 0.94,
            "capacity_fit": 0.96,
            "dietary_match": 1.0,
            "reliability": 0.97,
            "need_urgency": 0.90,
            "total_score": 0.95,
            "explanation": "Exceptional spatial fit in Gwalior (2.1km) with 300kg capacity accommodating 45kg hot banquet.",
        },
        "status": OfferStatus.OFFERED.value,
        "response_timeout_seconds": 600,
        "offered_at": (now - timedelta(minutes=3)).isoformat(),
        "expires_at": (now + timedelta(minutes=7)).isoformat(),
    }
    db.set_document("offers", active_offer_gwl["id"], active_offer_gwl)

    # 6. Active volunteer route for vol_arun_kumar (volunteer@gmail.com)
    volunteer_route = {
        "id": "rt_opt_blr_01",
        "volunteer_id": "vol_arun_kumar",
        "volunteer_name": "Arun Kumar",
        "stops": [
            {
                "stop_id": "stop_p1",
                "stop_type": "pickup",
                "listing_id": "list_wedding_rush_1",
                "target_name": "Taj Palace Luxury Catering",
                "location": {"latitude": 12.9716, "longitude": 77.5946},
                "estimated_arrival": (now + timedelta(minutes=15)).isoformat(),
                "deadline": (now + timedelta(minutes=90)).isoformat(),
                "completed": False,
            },
            {
                "stop_id": "stop_d1",
                "stop_type": "delivery",
                "listing_id": "list_wedding_rush_1",
                "target_name": "Robin Hood Army Indiranagar",
                "location": {"latitude": 12.9784, "longitude": 77.6408},
                "estimated_arrival": (now + timedelta(minutes=45)).isoformat(),
                "deadline": (now + timedelta(minutes=120)).isoformat(),
                "completed": False,
            },
        ],
        "total_distance_km": 6.8,
        "estimated_duration_mins": 45.0,
        "status": RouteStatus.ASSIGNED.value,
    }
    db.set_document("routes", volunteer_route["id"], volunteer_route)

    # 6b. Active volunteer route for vol_gwalior_vikram (gwalior.volunteer@gmail.com)
    volunteer_route_gwl = {
        "id": "rt_opt_gwl_01",
        "volunteer_id": "vol_gwalior_vikram",
        "volunteer_name": "Gwalior Rapid Courier Vikram",
        "stops": [
            {
                "stop_id": "stop_gwl_p1",
                "stop_type": "pickup",
                "listing_id": "list_gwalior_wedding_feast",
                "target_name": "Gwalior Heritage Palace Catering (Lashkar)",
                "location": {"latitude": 26.2045, "longitude": 78.1560},
                "estimated_arrival": (now + timedelta(minutes=10)).isoformat(),
                "deadline": (now + timedelta(minutes=75)).isoformat(),
                "completed": False,
            },
            {
                "stop_id": "stop_gwl_d1",
                "stop_type": "delivery",
                "listing_id": "list_gwalior_wedding_feast",
                "target_name": "Gwalior Annapurna Food Bank (City Center)",
                "location": {"latitude": 26.2124, "longitude": 78.1772},
                "estimated_arrival": (now + timedelta(minutes=28)).isoformat(),
                "deadline": (now + timedelta(minutes=105)).isoformat(),
                "completed": False,
            },
        ],
        "total_distance_km": 3.2,
        "estimated_duration_mins": 18.0,
        "status": RouteStatus.ASSIGNED.value,
    }
    db.set_document("routes", volunteer_route_gwl["id"], volunteer_route_gwl)

    # 7. Verification requests
    verifications = [
        {
            "id": "req_gwl_01",
            "name": "Gwalior Heritage Palace Catering",
            "email": "gwalior.palace.donor@gmail.com",
            "type": "donor",
            "fssai_license": "10423001000542",
            "address": "Jayaji Chowk, Lashkar, Gwalior, MP",
            "status": "verified",
            "submitted_at": (now - timedelta(days=2)).isoformat(),
        },
        {
            "id": "req_gwl_02",
            "name": "Gwalior Annapurna Food Bank",
            "email": "gwalior.annapurna.ngo@gmail.com",
            "type": "ngo",
            "fssai_license": "NGO-MP-474011",
            "address": "Patel Nagar, City Center, Gwalior, MP",
            "status": "verified",
            "submitted_at": (now - timedelta(days=3)).isoformat(),
        },
        {
            "id": "req_gwl_03",
            "name": "Gwalior Robin Hood Relief",
            "email": "gwalior.relief.ngo@gmail.com",
            "type": "ngo",
            "fssai_license": "NGO-MP-474006",
            "address": "Mall Road, Morar Cantt, Gwalior, MP",
            "status": "verified",
            "submitted_at": (now - timedelta(days=4)).isoformat(),
        },
        {
            "id": "req_gwl_04",
            "name": "Gwalior Central Banquets & Sweets",
            "email": "gwalior.banquets.donor@gmail.com",
            "type": "donor",
            "fssai_license": "10423001000889",
            "address": "Station Road, Padav, Gwalior, MP",
            "status": "verified",
            "submitted_at": (now - timedelta(days=1)).isoformat(),
        },
        {
            "id": "req_gwl_05",
            "name": "Gwalior Chambal Rasoi Seva Trust",
            "email": "chambal.rasoi.gwalior@gmail.com",
            "type": "ngo",
            "fssai_license": "NGO-MP-474015",
            "address": "Mayur Nagar, Thatipur, Gwalior, MP",
            "status": "pending",
            "submitted_at": (now - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "req_01",
            "name": "ITC Gardenia Banquets",
            "type": "donor",
            "fssai_license": "11223344556677",
            "address": "Residency Road, Bangalore",
            "status": "pending",
            "submitted_at": (now - timedelta(hours=3)).isoformat(),
        },
        {
            "id": "req_02",
            "name": "Hasiru Dala Feeding Centre",
            "type": "ngo",
            "fssai_license": "NGO-8829-KA",
            "address": "KR Market, Bangalore",
            "status": "pending",
            "submitted_at": (now - timedelta(hours=5)).isoformat(),
        },
        {
            "id": "req_03",
            "name": "Marriott Convention Center",
            "type": "donor",
            "fssai_license": "11899223344551",
            "address": "Whitefield, Bangalore",
            "status": "pending",
            "submitted_at": (now - timedelta(hours=1)).isoformat(),
        },
    ]
    for v in verifications:
        db.set_document("verifications", v["id"], v)

    # 8. Escalations
    escalations = [
        {
            "id": "esc_101",
            "listing_id": "list_wedding_rush_3",
            "donor": "Royal Orchid Hotel",
            "reason": "No responses within 15km. Search radius broadened to 30km.",
            "timestamp": "12m ago",
            "resolved": False,
        },
        {
            "id": "esc_100",
            "listing_id": "list_lunch_rush_1",
            "donor": "Taj Caterers",
            "reason": "Rank 1 NGO response timeout. Escalated to Koramangala Kitchen.",
            "timestamp": "34m ago",
            "resolved": True,
        },
    ]
    for e in escalations:
        db.set_document("escalations", e["id"], e)

    # 9. Baseline impact records
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "impact_calc", root_dir / "services" / "analytics-service" / "app" / "impact.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    calc = mod.ImpactCalculator()
    calc.record_completed_pickup("list_prev_01", "donor_taj_palace", "ngo_robin_hood", 65.0, 180)
    calc.record_completed_pickup("list_prev_02", "donor_grand_banquet", "ngo_koramangala", 45.0, 125)

    print("Successfully seeded FoodBridge database with realistic entities!")


if __name__ == "__main__":
    seed_database()

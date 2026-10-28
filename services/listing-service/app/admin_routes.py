import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import urllib.request
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from shared.firestore_client import get_firestore_client
from shared.logging_setup import setup_logger

logger = setup_logger("admin_routes")
router = APIRouter(prefix="/admin", tags=["admin"])
db = get_firestore_client()

VERIFICATIONS_COLLECTION = "verifications"
ESCALATIONS_COLLECTION = "escalations"
TRANSFERS_COLLECTION = "transfers"

INITIAL_TRANSFERS = [
    {
        "id": "tr_gwl_01",
        "listing_id": "list_gwalior_wedding_feast",
        "food_title": "Royal Gwalior Shaadi Banquet Feast - Dal Makhani, Paneer Lababdar & Jeera Pulao",
        "category": "cooked_meals",
        "quantity_kg": 45,
        "portions": 130,
        "city": "Gwalior",
        "donor_id": "donor_gwl_palace",
        "donor_name": "Gwalior Heritage Palace Catering",
        "donor_address": "Jayaji Chowk, Lashkar, Gwalior",
        "ngo_id": "ngo_gwl_annapurna",
        "ngo_name": "Gwalior Annapurna Food Bank",
        "ngo_address": "Patel Nagar, City Center, Gwalior",
        "volunteer_id": "vol_gwl_vikram",
        "volunteer_name": "Vikram Rathore (Gwalior Courier)",
        "current_status": "in_transit",
        "temperature_log": "67.2°C (Safe Hot-Hold)",
        "thermal_safety_ok": True,
        "co2e_saved_kg": 112.5,
        "eta": "14 mins",
        "distance_km": 3.8,
        "created_at": "2026-10-28T18:30:00Z",
        "updated_at": "2026-10-28T18:50:00Z",
        "transitions": [
            {
                "stage": "posted",
                "label": "Surplus Registered",
                "timestamp": "18:30:00",
                "completed": True,
                "current": False,
                "actor": "Donor: Gwalior Heritage Palace",
                "details": "Surplus logged: 45kg (130 portions). Gemini AI vision inspection passed (Confidence 94%). Safe until 23:30.",
            },
            {
                "stage": "offered",
                "label": "Cascade Dispatched",
                "timestamp": "18:32:00",
                "completed": True,
                "current": False,
                "actor": "Cascade Matching Engine",
                "details": "Rank #1 Offer sent to Gwalior Annapurna Food Bank (Score 0.94, Proximity 3.8km, 5m timer active).",
            },
            {
                "stage": "matched",
                "label": "Claimed by NGO",
                "timestamp": "18:35:00",
                "completed": True,
                "current": False,
                "actor": "NGO: Gwalior Annapurna Food Bank",
                "details": "Offer accepted for 130 beneficiaries. Courier route generated and assigned to Vikram Rathore.",
            },
            {
                "stage": "in_transit",
                "label": "Picked Up & En Route",
                "timestamp": "18:50:00",
                "completed": False,
                "current": True,
                "actor": "Courier: Vikram Rathore",
                "details": "Courier pickup verified at Jayaji Chowk. Calibrated digital thermal probe: 67.2°C logged. En route to City Center.",
            },
            {
                "stage": "completed",
                "label": "Delivery & Verification",
                "timestamp": "Pending",
                "completed": False,
                "current": False,
                "actor": "Receiving Shelter Staff",
                "details": "Scheduled handover at Patel Nagar Community Kitchen. Tamper seal scan and CSR issuance pending.",
            },
        ],
    },
    {
        "id": "tr_gwl_02",
        "listing_id": "list_gwl_banquet_sweets",
        "food_title": "Gwalior Gulab Jamun, Moong Dal Halwa & Poori Sabzi",
        "category": "cooked_meals",
        "quantity_kg": 22,
        "portions": 70,
        "city": "Gwalior",
        "donor_id": "donor_gwl_banquets",
        "donor_name": "Gwalior Central Banquets & Sweets",
        "donor_address": "Station Road, Padav, Gwalior",
        "ngo_id": "ngo_gwl_relief",
        "ngo_name": "Gwalior Robin Hood Relief",
        "ngo_address": "Mall Road, Morar Cantt, Gwalior",
        "volunteer_id": "vol_gwl_vikram",
        "volunteer_name": "Vikram Rathore (Gwalior Courier)",
        "current_status": "offered",
        "temperature_log": "63.5°C (Warm Hold)",
        "thermal_safety_ok": True,
        "co2e_saved_kg": 55.0,
        "eta": "Awaiting NGO Claim",
        "distance_km": 4.1,
        "created_at": "2026-10-28T19:15:00Z",
        "updated_at": "2026-10-28T19:17:00Z",
        "transitions": [
            {
                "stage": "posted",
                "label": "Surplus Registered",
                "timestamp": "19:15:00",
                "completed": True,
                "current": False,
                "actor": "Donor: Gwalior Central Banquets",
                "details": "Surplus logged: 22kg (70 portions). Fresh sweets & dinner items verified under FSSAI hot-hold norms.",
            },
            {
                "stage": "offered",
                "label": "Cascade Dispatched",
                "timestamp": "19:17:00",
                "completed": False,
                "current": True,
                "actor": "Cascade Matching Engine",
                "details": "Dispatched to Gwalior Robin Hood Relief (Rank #1, 4.1km away). 5-minute timeout window active.",
            },
            {
                "stage": "matched",
                "label": "NGO Acceptance",
                "timestamp": "Pending",
                "completed": False,
                "current": False,
                "actor": "NGO Dispatcher",
                "details": "Awaiting claim confirmation from Morar Cantt center coordinator.",
            },
            {
                "stage": "in_transit",
                "label": "Courier Transport",
                "timestamp": "Pending",
                "completed": False,
                "current": False,
                "actor": "Volunteer Fleet",
                "details": "Pending NGO claim before vehicle dispatch.",
            },
            {
                "stage": "completed",
                "label": "Shelter Handover",
                "timestamp": "Pending",
                "completed": False,
                "current": False,
                "actor": "Shelter Receiving Desk",
                "details": "Delivery verification & CSR certificate generation scheduled.",
            },
        ],
    },
    {
        "id": "tr_gwl_03",
        "listing_id": "list_gwl_chambal_lunch",
        "food_title": "Fresh Tawa Roti, Dal Tadka & Aloo Gobhi Sabzi",
        "category": "cooked_meals",
        "quantity_kg": 32,
        "portions": 95,
        "city": "Gwalior",
        "donor_id": "donor_gwl_palace",
        "donor_name": "Gwalior Heritage Palace Catering",
        "donor_address": "Jayaji Chowk, Lashkar, Gwalior",
        "ngo_id": "ngo_gwl_chambal",
        "ngo_name": "Gwalior Chambal Rasoi Seva Trust",
        "ngo_address": "Mayur Nagar, Thatipur, Gwalior",
        "volunteer_id": "vol_gwl_vikram",
        "volunteer_name": "Vikram Rathore (Gwalior Courier)",
        "current_status": "completed",
        "temperature_log": "66.5°C (Shelter Verified)",
        "thermal_safety_ok": True,
        "co2e_saved_kg": 80.0,
        "eta": "Delivered at 13:48",
        "distance_km": 5.2,
        "certificate_id": "CSR-GWL-2026-9041",
        "created_at": "2026-10-28T13:00:00Z",
        "updated_at": "2026-10-28T13:48:00Z",
        "transitions": [
            {
                "stage": "posted",
                "label": "Surplus Registered",
                "timestamp": "13:00:00",
                "completed": True,
                "current": False,
                "actor": "Donor: Gwalior Heritage Palace",
                "details": "Lunch banquet surplus: 32kg (95 portions). Packaged in insulated Cambro containers.",
            },
            {
                "stage": "offered",
                "label": "Cascade Dispatched",
                "timestamp": "13:02:00",
                "completed": True,
                "current": False,
                "actor": "Cascade Matching Engine",
                "details": "Offered to Chambal Rasoi Seva Trust based on shelter meal requirements.",
            },
            {
                "stage": "matched",
                "label": "Claimed by NGO",
                "timestamp": "13:05:00",
                "completed": True,
                "current": False,
                "actor": "NGO: Chambal Rasoi Seva Trust",
                "details": "Accepted. Pickup route dispatched to courier Vikram Rathore.",
            },
            {
                "stage": "in_transit",
                "label": "Picked Up & En Route",
                "timestamp": "13:20:00",
                "completed": True,
                "current": False,
                "actor": "Courier: Vikram Rathore",
                "details": "Picked up from Lashkar. Thermal probe verified at 68.4°C. Transit time: 24 mins.",
            },
            {
                "stage": "completed",
                "label": "Verified & Distributed",
                "timestamp": "13:48:00",
                "completed": True,
                "current": True,
                "actor": "Shelter Desk & Volunteer",
                "details": "95 meals distributed to Thatipur night shelter residents. Handover QR scanned. CSR cert #CSR-GWL-2026-9041 issued.",
            },
        ],
    },
    {
        "id": "tr_blr_01",
        "listing_id": "list_taj_biryani_feast",
        "food_title": "Royal Hyderabadi Dum Biryani & Mirchi Ka Salan (42 kg)",
        "category": "cooked_meals",
        "quantity_kg": 42,
        "portions": 120,
        "city": "Bangalore",
        "donor_id": "donor_taj",
        "donor_name": "Taj Palace Luxury Catering",
        "donor_address": "MG Road, Bangalore",
        "ngo_id": "ngo_robin_hood",
        "ngo_name": "Robin Hood Army Bangalore",
        "ngo_address": "100ft Rd, Indiranagar, Bangalore",
        "volunteer_id": "vol_arun",
        "volunteer_name": "Arun Kumar",
        "current_status": "completed",
        "temperature_log": "68.0°C (Insulated Hot Box)",
        "thermal_safety_ok": True,
        "co2e_saved_kg": 105.0,
        "eta": "Delivered at 15:05",
        "distance_km": 4.6,
        "certificate_id": "CSR-BLR-2026-7812",
        "created_at": "2026-10-28T14:15:00Z",
        "updated_at": "2026-10-28T15:05:00Z",
        "transitions": [
            {
                "stage": "posted",
                "label": "Surplus Registered",
                "timestamp": "14:15:00",
                "completed": True,
                "current": False,
                "actor": "Executive Chef, Taj Palace",
                "details": "42 kg Hyderabadi Biryani posted with AI vision freshness check (Grade A, 96% confidence).",
            },
            {
                "stage": "offered",
                "label": "Cascade Dispatched",
                "timestamp": "14:17:00",
                "completed": True,
                "current": False,
                "actor": "Cascade Matching Engine",
                "details": "Dispatched to Robin Hood Army Bangalore (Rank #1, proximity 4.6km).",
            },
            {
                "stage": "matched",
                "label": "Claimed by NGO",
                "timestamp": "14:19:00",
                "completed": True,
                "current": False,
                "actor": "NGO Coordinator: Robin Hood Army",
                "details": "Claimed within 2 minutes. Courier Arun Kumar assigned via automated dispatch.",
            },
            {
                "stage": "in_transit",
                "label": "Picked Up & En Route",
                "timestamp": "14:35:00",
                "completed": True,
                "current": False,
                "actor": "Courier: Arun Kumar",
                "details": "Courier pickup confirmed at Taj kitchen bay. Thermal probe verified 68.0°C. Temperature logged in DynamoDB.",
            },
            {
                "stage": "completed",
                "label": "Handover Verified",
                "timestamp": "15:05:00",
                "completed": True,
                "current": True,
                "actor": "Shelter Lead: Indiranagar",
                "details": "Delivery verified with zero seal tamper. 120 beneficiaries fed. Cryptographic CSR cert #CSR-BLR-2026-7812 issued.",
            },
        ],
    },
    {
        "id": "tr_blr_02",
        "listing_id": "list_marriott_curry_spread",
        "food_title": "Paneer Butter Masala, Mixed Veg Curry & Butter Naan",
        "category": "cooked_meals",
        "quantity_kg": 28,
        "portions": 85,
        "city": "Bangalore",
        "donor_id": "donor_marriott",
        "donor_name": "Grand Convention & Banquets",
        "donor_address": "Whitefield, Bangalore",
        "ngo_id": "ngo_koramangala",
        "ngo_name": "Koramangala Kitchen",
        "ngo_address": "Koramangala 4th Block, Bangalore",
        "volunteer_id": "vol_priya",
        "volunteer_name": "Priya Sharma",
        "current_status": "matched",
        "temperature_log": "65.8°C (Pre-Pickup Probe)",
        "thermal_safety_ok": True,
        "co2e_saved_kg": 70.0,
        "eta": "Courier Arriving in 8 mins",
        "distance_km": 6.8,
        "created_at": "2026-10-28T19:40:00Z",
        "updated_at": "2026-10-28T19:46:00Z",
        "transitions": [
            {
                "stage": "posted",
                "label": "Surplus Registered",
                "timestamp": "19:40:00",
                "completed": True,
                "current": False,
                "actor": "Banquet Manager: Grand Convention",
                "details": "Post-conference surplus: 28kg cooked North Indian cuisine. Packaged in sanitized food-grade trays.",
            },
            {
                "stage": "offered",
                "label": "Cascade Dispatched",
                "timestamp": "19:42:00",
                "completed": True,
                "current": False,
                "actor": "Cascade Matching Engine",
                "details": "Automated matching score: 0.91 based on Koramangala Kitchen meal schedule.",
            },
            {
                "stage": "matched",
                "label": "Claimed by NGO",
                "timestamp": "19:46:00",
                "completed": False,
                "current": True,
                "actor": "NGO Coordinator & Courier Priya",
                "details": "Offer claimed. Volunteer Priya Sharma accepted transit assignment. En route to Whitefield pickup bay.",
            },
            {
                "stage": "in_transit",
                "label": "Pickup & Thermal Check",
                "timestamp": "Pending",
                "completed": False,
                "current": False,
                "actor": "Courier: Priya Sharma",
                "details": "Digital probe verification pending at loading bay.",
            },
            {
                "stage": "completed",
                "label": "Shelter Receipt",
                "timestamp": "Pending",
                "completed": False,
                "current": False,
                "actor": "Shelter Kitchen Supervisor",
                "details": "Handover scan and distribution log pending.",
            },
        ],
    },
    {
        "id": "tr_blr_03",
        "listing_id": "list_orchard_bakery_pastry",
        "food_title": "Assorted Artisan Breads, Wholewheat Rolls & Pastries",
        "category": "bakery",
        "quantity_kg": 15,
        "portions": 45,
        "city": "Bangalore",
        "donor_id": "donor_bakery",
        "donor_name": "The Orchard Bakery & Cafe",
        "donor_address": "Indiranagar 12th Main, Bangalore",
        "ngo_id": "ngo_robin_hood",
        "ngo_name": "Robin Hood Army Bangalore",
        "ngo_address": "100ft Rd, Indiranagar, Bangalore",
        "volunteer_id": "vol_kavita",
        "volunteer_name": "Kavita Reddy",
        "current_status": "in_transit",
        "temperature_log": "21.4°C (Ambient Dry Safe)",
        "thermal_safety_ok": True,
        "co2e_saved_kg": 37.5,
        "eta": "9 mins",
        "distance_km": 1.9,
        "created_at": "2026-10-28T20:00:00Z",
        "updated_at": "2026-10-28T20:20:00Z",
        "transitions": [
            {
                "stage": "posted",
                "label": "Surplus Registered",
                "timestamp": "20:00:00",
                "completed": True,
                "current": False,
                "actor": "The Orchard Bakery Lead",
                "details": "15 kg freshly baked breads and rolls packed in moisture-resistant breathable bakery cartons.",
            },
            {
                "stage": "offered",
                "label": "Cascade Dispatched",
                "timestamp": "20:02:00",
                "completed": True,
                "current": False,
                "actor": "Cascade Matching Engine",
                "details": "High proximity match (1.9km) offered to Robin Hood Army youth center.",
            },
            {
                "stage": "matched",
                "label": "Claimed by NGO",
                "timestamp": "20:05:00",
                "completed": True,
                "current": False,
                "actor": "NGO: Robin Hood Army",
                "details": "Accepted. Courier Kavita Reddy assigned for rapid localized pickup.",
            },
            {
                "stage": "in_transit",
                "label": "Picked Up & En Route",
                "timestamp": "20:20:00",
                "completed": False,
                "current": True,
                "actor": "Courier: Kavita Reddy",
                "details": "Package collected. Clean seal confirmed. Courier on route via 100ft Road.",
            },
            {
                "stage": "completed",
                "label": "Final Handover",
                "timestamp": "Pending",
                "completed": False,
                "current": False,
                "actor": "Shelter Receiving Desk",
                "details": "Scheduled distribution for evening shelter snack program.",
            },
        ],
    },
]


def _ensure_initial_admin_data():
    existing_ver = db.query_collection(VERIFICATIONS_COLLECTION)
    existing_ids = {v["id"] for v in existing_ver}
    for v in INITIAL_VERIFICATIONS:
        if v["id"] not in existing_ids:
            db.set_document(VERIFICATIONS_COLLECTION, v["id"], v)

    existing_esc = db.query_collection(ESCALATIONS_COLLECTION)
    existing_esc_ids = {e["id"] for e in existing_esc}
    for e in INITIAL_ESCALATIONS:
        if e["id"] not in existing_esc_ids:
            db.set_document(ESCALATIONS_COLLECTION, e["id"], e)

    existing_transfers = db.query_collection(TRANSFERS_COLLECTION)
    existing_tr_ids = {t["id"] for t in existing_transfers}
    for tr in INITIAL_TRANSFERS:
        if tr["id"] not in existing_tr_ids:
            db.set_document(TRANSFERS_COLLECTION, tr["id"], tr)



class PartnerApplicationRequest(BaseModel):
    name: str
    email: str
    type: str  # "donor" or "ngo"
    fssai_license: str
    address: str
    phone: Optional[str] = "+91 98765 00000"
    password: Optional[str] = "1234"

# Default pre-seeded verification requests if database collection is empty
INITIAL_VERIFICATIONS = [
    {
        "id": "req_gwl_01",
        "name": "Gwalior Heritage Palace Catering",
        "email": "gwalior.palace.donor@gmail.com",
        "type": "donor",
        "fssai_license": "10423001000542",
        "address": "Jayaji Chowk, Lashkar, Gwalior, MP",
        "phone": "+91 98765 77005",
        "password": "1234",
        "status": "verified",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_gwl_02",
        "name": "Gwalior Annapurna Food Bank",
        "email": "gwalior.annapurna.ngo@gmail.com",
        "type": "ngo",
        "fssai_license": "NGO-MP-474011",
        "address": "Patel Nagar, City Center, Gwalior, MP",
        "phone": "+91 98765 77002",
        "password": "1234",
        "status": "verified",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_gwl_03",
        "name": "Gwalior Robin Hood Relief",
        "email": "gwalior.relief.ngo@gmail.com",
        "type": "ngo",
        "fssai_license": "NGO-MP-474006",
        "address": "Mall Road, Morar Cantt, Gwalior, MP",
        "phone": "+91 98765 77003",
        "password": "1234",
        "status": "verified",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_gwl_04",
        "name": "Gwalior Central Banquets & Sweets",
        "email": "gwalior.banquets.donor@gmail.com",
        "type": "donor",
        "fssai_license": "10423001000889",
        "address": "Station Road, Padav, Gwalior, MP",
        "phone": "+91 98765 77006",
        "password": "1234",
        "status": "verified",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_gwl_05",
        "name": "Gwalior Chambal Rasoi Seva Trust",
        "email": "chambal.rasoi.gwalior@gmail.com",
        "type": "ngo",
        "fssai_license": "NGO-MP-474015",
        "address": "Mayur Nagar, Thatipur, Gwalior, MP",
        "phone": "+91 98765 77010",
        "password": "1234",
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_01",
        "name": "ITC Gardenia Banquets",
        "email": "itc@gardenia.com",
        "type": "donor",
        "fssai_license": "11223344556677",
        "address": "Residency Road, Bangalore",
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_02",
        "name": "Hasiru Dala Feeding Centre",
        "email": "hasiru@feeding.org",
        "type": "ngo",
        "fssai_license": "NGO-8829-KA",
        "address": "KR Market, Bangalore",
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "req_03",
        "name": "Marriott Convention Center",
        "email": "marriott@whitefield.com",
        "type": "donor",
        "fssai_license": "11899223344551",
        "address": "Whitefield, Bangalore",
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    },
]

INITIAL_ESCALATIONS = [
    {
        "id": "esc_gwl_1",
        "listing_id": "list_gwalior_wedding_feast",
        "donor": "Gwalior Heritage Palace Catering",
        "reason": "Gwalior surplus volume alert: 45kg wedding banquet matched with high priority.",
        "timestamp": "4m ago",
        "resolved": False,
    },
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


def _ensure_initial_admin_data():
    existing_ver = db.query_collection(VERIFICATIONS_COLLECTION)
    existing_ids = {v["id"] for v in existing_ver}
    for v in INITIAL_VERIFICATIONS:
        if v["id"] not in existing_ids:
            db.set_document(VERIFICATIONS_COLLECTION, v["id"], v)

    existing_esc = db.query_collection(ESCALATIONS_COLLECTION)
    existing_esc_ids = {e["id"] for e in existing_esc}
    for e in INITIAL_ESCALATIONS:
        if e["id"] not in existing_esc_ids:
            db.set_document(ESCALATIONS_COLLECTION, e["id"], e)


@router.post("/verifications/apply")
def apply_for_verification(payload: PartnerApplicationRequest) -> Dict[str, Any]:
    """Allows a new donor or NGO to apply for verified partnership."""
    req_id = f"req_{uuid.uuid4().hex[:8]}"
    pwd = payload.password if payload.password else "1234"
    doc = {
        "id": req_id,
        "name": payload.name,
        "email": payload.email.strip().lower(),
        "type": payload.type.strip().lower(),
        "fssai_license": payload.fssai_license,
        "address": payload.address,
        "phone": payload.phone,
        "password": pwd,
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    db.set_document(VERIFICATIONS_COLLECTION, req_id, doc)

    # Also register in user profiles as pending
    user_uid = f"{payload.type.strip().lower()}_{uuid.uuid4().hex[:6]}"
    user_doc = {
        "uid": user_uid,
        "email": payload.email.strip().lower(),
        "name": payload.name,
        "role": payload.type.strip().lower(),
        "phone": payload.phone,
        "password": pwd,
        "verification_status": "pending",
        "fssai_license": payload.fssai_license,
    }
    db.set_document("users", user_uid, user_doc)
    logger.info(f"Registered partner application {req_id} for {payload.name} ({payload.email})")
    return doc


@router.get("/verifications")
def get_verification_queue() -> List[Dict[str, Any]]:
    """Retrieves all partner organization verification requests."""
    _ensure_initial_admin_data()
    return db.query_collection(VERIFICATIONS_COLLECTION, order_by="-submitted_at")


@router.get("/verifications/status/{email}")
def get_partner_verification_status(email: str) -> Dict[str, Any]:
    """Retrieves current verification and account status for a given email."""
    norm_email = email.strip().lower()
    vers = db.query_collection(VERIFICATIONS_COLLECTION, filters=[("email", "==", norm_email)])
    if vers:
        # Return the latest one
        v = sorted(vers, key=lambda x: str(x.get("submitted_at", "")), reverse=True)[0]
        return {
            "found": True,
            "status": v.get("status", "pending"),
            "id": v.get("id"),
            "name": v.get("name"),
            "email": v.get("email"),
            "type": v.get("type"),
            "password": v.get("password", "1234"),
            "phone": v.get("phone"),
            "address": v.get("address"),
            "fssai_license": v.get("fssai_license"),
            "verified_at": v.get("verified_at"),
        }

    # Fallback to users collection
    users = db.query_collection("users", filters=[("email", "==", norm_email)])
    if users:
        u = users[0]
        return {
            "found": True,
            "status": u.get("verification_status", "verified"),
            "name": u.get("name"),
            "email": u.get("email"),
            "type": u.get("role"),
            "password": u.get("password", "1234"),
            "phone": u.get("phone"),
            "fssai_license": u.get("fssai_license"),
        }

    return {"found": False}


@router.post("/verifications/{req_id}/approve")
def approve_verification(req_id: str) -> Dict[str, Any]:
    """Approves a partner and updates verification status in database."""
    doc = db.get_document(VERIFICATIONS_COLLECTION, req_id)
    if not doc:
        doc = {"id": req_id, "status": "pending"}

    doc["status"] = "verified"
    doc["verified_at"] = datetime.now(timezone.utc).isoformat()
    db.set_document(VERIFICATIONS_COLLECTION, req_id, doc)

    # Sync verification_status across users collection
    if doc.get("email"):
        users = db.query_collection("users", filters=[("email", "==", doc["email"])])
        for u in users:
            u["verification_status"] = "verified"
            db.set_document("users", u["uid"], u)

    logger.info(f"Admin approved verification request {req_id} ({doc.get('email')})")
    return doc


@router.post("/verifications/{req_id}/reject")
def reject_verification(req_id: str) -> Dict[str, Any]:
    """Rejects a partner verification request in database."""
    doc = db.get_document(VERIFICATIONS_COLLECTION, req_id)
    if not doc:
        doc = {"id": req_id, "status": "pending"}

    doc["status"] = "rejected"
    doc["rejected_at"] = datetime.now(timezone.utc).isoformat()
    db.set_document(VERIFICATIONS_COLLECTION, req_id, doc)

    if doc.get("email"):
        users = db.query_collection("users", filters=[("email", "==", doc["email"])])
        for u in users:
            u["verification_status"] = "rejected"
            db.set_document("users", u["uid"], u)

    logger.info(f"Admin rejected verification request {req_id} ({doc.get('email')})")
    return doc


@router.get("/escalations")
def get_escalations() -> List[Dict[str, Any]]:
    """Retrieves all matching escalation alerts."""
    _ensure_initial_admin_data()
    return db.query_collection(ESCALATIONS_COLLECTION)


@router.post("/escalations/{esc_id}/resolve")
def resolve_escalation(esc_id: str) -> Dict[str, Any]:
    """Resolves an escalation alert in the database."""
    doc = db.get_document(ESCALATIONS_COLLECTION, esc_id)
    if not doc:
        doc = {"id": esc_id, "resolved": False}

    doc["resolved"] = True
    doc["resolved_at"] = datetime.now(timezone.utc).isoformat()
    db.set_document(ESCALATIONS_COLLECTION, esc_id, doc)
    logger.info(f"Admin resolved escalation {esc_id}")
    return doc


@router.get("/health-telemetry")
def get_health_telemetry() -> Dict[str, Any]:
    """Actively probes the status and latency of all FoodBridge serverless microservices."""
    endpoints = {
        "listing-service": ("http://127.0.0.1:8001/health", 8001),
        "matching-service": ("http://127.0.0.1:8002/health", 8002),
        "notification-service": ("http://127.0.0.1:8003/health", 8003),
        "logistics-service": ("http://127.0.0.1:8004/health", 8004),
        "analytics-service": ("http://127.0.0.1:8005/health", 8005),
        "expiry-job": ("http://127.0.0.1:8006/health", 8006),
    }

    results = {}
    for name, (url, port) in endpoints.items():
        t0 = time.time()
        is_healthy = False
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "FoodBridgeAdminProbe"})
            with urllib.request.urlopen(req, timeout=0.6) as response:
                if response.status == 200:
                    is_healthy = True
        except Exception:
            # Fallback if listing-service is self
            is_healthy = (name == "listing-service")

        latency_ms = round((time.time() - t0) * 1000, 1)
        results[name] = {
            "healthy": is_healthy,
            "port": port,
            "latency_ms": latency_ms if is_healthy else None,
        }

    return results


@router.get("/transfers")
def get_recent_transfers() -> List[Dict[str, Any]]:
    """Retrieves all recent food transfers and their lifecycle transition status."""
    _ensure_initial_admin_data()
    transfers = db.query_collection(TRANSFERS_COLLECTION)
    status_priority = {"in_transit": 0, "matched": 1, "offered": 2, "posted": 3, "completed": 4, "cancelled": 5}
    return sorted(transfers, key=lambda t: (status_priority.get(t.get("current_status"), 99), str(t.get("updated_at", ""))), reverse=False)


@router.post("/transfers/{transfer_id}/advance")
def advance_transfer_stage(transfer_id: str) -> Dict[str, Any]:
    """Advances a food transfer through its lifecycle stages: posted -> offered -> matched -> in_transit -> completed."""
    _ensure_initial_admin_data()
    doc = db.get_document(TRANSFERS_COLLECTION, transfer_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Transfer not found")

    stages = ["posted", "offered", "matched", "in_transit", "completed"]
    curr = doc.get("current_status", "posted")
    try:
        curr_idx = stages.index(curr)
    except ValueError:
        curr_idx = 0

    if curr_idx >= len(stages) - 1:
        return doc

    next_idx = curr_idx + 1
    next_stage = stages[next_idx]
    now_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
    now_iso = datetime.now(timezone.utc).isoformat()

    doc["current_status"] = next_stage
    doc["updated_at"] = now_iso

    transitions = doc.get("transitions", [])
    for tr in transitions:
        if tr.get("stage") == curr:
            tr["completed"] = True
            tr["current"] = False
        elif tr.get("stage") == next_stage:
            tr["completed"] = (next_stage == "completed")
            tr["current"] = True
            tr["timestamp"] = now_str
            if next_stage == "in_transit":
                tr["details"] = f"Courier pickup logged. Digital thermal probe verified at {doc.get('temperature_log', '66.8°C')}."
            elif next_stage == "completed":
                tr["details"] = "Delivery successfully completed. Receiver QR scanned, temperature & weight verified."

    if next_stage == "completed":
        doc["eta"] = f"Delivered at {now_str}"
        if not doc.get("certificate_id"):
            city_prefix = "GWL" if doc.get("city") == "Gwalior" else "BLR"
            doc["certificate_id"] = f"CSR-{city_prefix}-2026-{uuid.uuid4().hex[:4].upper()}"

    db.set_document(TRANSFERS_COLLECTION, transfer_id, doc)
    logger.info(f"Advanced transfer {transfer_id} from {curr} to {next_stage}")
    return doc


@router.post("/transfers/{transfer_id}/reset")
def reset_transfer_stage(transfer_id: str) -> Dict[str, Any]:
    """Resets a transfer back to original state for demo replay."""
    for init_tr in INITIAL_TRANSFERS:
        if init_tr["id"] == transfer_id:
            import copy
            reset_doc = copy.deepcopy(init_tr)
            db.set_document(TRANSFERS_COLLECTION, transfer_id, reset_doc)
            return reset_doc
    raise HTTPException(status_code=404, detail="Transfer blueprint not found")


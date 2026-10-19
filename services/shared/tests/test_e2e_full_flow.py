import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
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

import importlib
import importlib.util
root_dir = Path(__file__).resolve().parent.parent.parent

def import_service_module(service_name, module_rel_path):
    srv_dir = str(root_dir / service_name)
    if srv_dir not in sys.path:
        sys.path.insert(0, srv_dir)
    for k in list(sys.modules.keys()):
        if k == "app" or k.startswith("app."):
            del sys.modules[k]
    module_path = root_dir / service_name / "app" / f"{module_rel_path}.py"
    spec = importlib.util.spec_from_file_location(f"app.{module_rel_path}", module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"app.{module_rel_path}"] = mod
    spec.loader.exec_module(mod)
    return mod

cascade_mod = import_service_module("matching-service", "cascade")
CascadeManager = cascade_mod.CascadeManager

templates_mod = import_service_module("notification-service", "templates")
template_match_offered = templates_mod.template_match_offered
template_offer_accepted = templates_mod.template_offer_accepted

fcm_mod = import_service_module("notification-service", "fcm")
dispatched_notifications = fcm_mod.dispatched_notifications

sms_mod = import_service_module("notification-service", "sms_provider")
MockSmsProvider = sms_mod.MockSmsProvider
get_sms_provider = sms_mod.get_sms_provider

optimizer_mod = import_service_module("logistics-service", "route_optimizer")
nearest_neighbor_route = optimizer_mod.nearest_neighbor_route
two_opt_optimize = optimizer_mod.two_opt_optimize

cert_mod = import_service_module("analytics-service", "certificate")
generate_csr_certificate_pdf = cert_mod.generate_csr_certificate_pdf

impact_mod = import_service_module("analytics-service", "impact")
ImpactCalculator = impact_mod.ImpactCalculator


def test_end_to_end_event_driven_pipeline():
    """Validates the entire lifecycle:
    Listing -> Spoilage Filter -> Matching Score -> Cascading Offer -> NGO Acceptance
    -> Volunteer Route Optimization -> Verified Handover -> Impact & CSR Certificate.
    """
    db = get_firestore_client()
    bus = get_event_bus()
    if isinstance(db, InMemoryFirestoreClient):
        db.clear()
    if isinstance(bus, InMemoryEventBus):
        bus.clear()

    sms_provider = get_sms_provider()
    if isinstance(sms_provider, MockSmsProvider):
        sms_provider.clear()
    dispatched_notifications.clear()

    now = datetime.now(timezone.utc)

    # 1. Seed Donor, NGO, Volunteer
    donor = UserProfile(
        uid="donor_taj",
        email="chef@taj.example",
        name="Taj Palace Luxury Catering",
        role=UserRole.DONOR,
        location=GeoPoint(latitude=12.9716, longitude=77.5946),
        verification_status=VerificationStatus.VERIFIED,
    )
    ngo = UserProfile(
        uid="ngo_robin_hood",
        email="ops@robinhood.example",
        name="Robin Hood Army Bangalore",
        role=UserRole.NGO,
        location=GeoPoint(latitude=12.9784, longitude=77.6408),  # 5km away
        capacity_kg=200.0,
        dietary_preferences=[DietaryType.ANY],
        reliability_score=0.98,
        verification_status=VerificationStatus.VERIFIED,
    )
    volunteer = UserProfile(
        uid="vol_arun",
        email="arun@vol.example",
        name="Arun Kumar",
        role=UserRole.VOLUNTEER,
        location=GeoPoint(latitude=12.9700, longitude=77.5900),
        verification_status=VerificationStatus.VERIFIED,
    )

    db.set_document("users", donor.uid, donor.model_dump(mode="json"))
    db.set_document("users", ngo.uid, ngo.model_dump(mode="json"))
    db.set_document("users", volunteer.uid, volunteer.model_dump(mode="json"))

    # 2. Wire up service event listeners on the event bus
    cascade = CascadeManager()
    impact_calc = ImpactCalculator()

    # Listener: listing.created -> matching cascade
    bus.subscribe("listing.created", lambda msg: cascade.process_new_listing(msg.data["listing_id"]))

    # Listener: match.offered -> notification
    def _on_match_offered(msg):
        tmpl = template_match_offered(msg.data)
        sms_provider.send_sms("+919876543211", tmpl["sms"])
    bus.subscribe("match.offered", _on_match_offered)

    # Listener: pickup.completed -> impact recording
    def _on_pickup_completed(msg):
        impact_calc.record_completed_pickup(
            listing_id=msg.data["listing_id"],
            donor_id=msg.data["donor_id"],
            ngo_id=msg.data["ngo_id"],
            quantity_kg=msg.data["quantity_kg"],
            portions=msg.data["portions"],
        )
    bus.subscribe("pickup.completed", _on_pickup_completed)

    # 3. Create a surplus food listing
    listing = DonorListing(
        id="list_wedding_delight",
        donor_id=donor.uid,
        donor_name=donor.name,
        title="Wedding Banquet Feast: Vegetable Pulao & Kofta",
        description="Freshly prepared hot food from wedding luncheon.",
        category=FoodCategory.COOKED_MEALS,
        storage_condition=StorageCondition.HOT_HOLD,
        dietary_type=DietaryType.VEG,
        quantity_kg=40.0,
        portions=120,
        prepared_at=now,
        safe_until=now + timedelta(hours=4),
        location=donor.location,
        geohash="tdr1vw",
        status=ListingStatus.AVAILABLE,
    )
    db.set_document("listings", listing.id, listing.model_dump(mode="json"))

    # 4. Emit listing.created event
    bus.publish("listing.created", {"listing_id": listing.id})

    # Verify Offer Created for Rank 1 NGO
    offers = db.query_collection("offers", filters=[("listing_id", "==", listing.id)])
    assert len(offers) == 1
    offer = offers[0]
    assert offer["ngo_id"] == ngo.uid
    assert offer["rank"] == 1
    assert offer["status"] == OfferStatus.OFFERED.value

    # Verify SMS notification sent
    if isinstance(sms_provider, MockSmsProvider):
        assert len(sms_provider.sent_messages) == 1
        assert "Urgent surplus" in sms_provider.sent_messages[0]["message"]

    # 5. NGO Accepts Offer
    accepted_offer, updated_listing = cascade.accept_offer(offer["id"], ngo_id=ngo.uid)
    assert accepted_offer.status == OfferStatus.ACCEPTED
    assert updated_listing.status == ListingStatus.CLAIMED

    # 6. Logistics: Volunteer Route Generation
    # Construct pickup & delivery stops
    from shared.models import RouteStop
    p_stop = RouteStop(
        stop_id="stop_pick_1",
        stop_type="pickup",
        listing_id=listing.id,
        target_name=donor.name,
        location=donor.location,
        estimated_arrival=now + timedelta(minutes=15),
        deadline=listing.safe_until - timedelta(minutes=30),
    )
    d_stop = RouteStop(
        stop_id="stop_del_1",
        stop_type="delivery",
        listing_id=listing.id,
        target_name=ngo.name,
        location=ngo.location,
        estimated_arrival=now + timedelta(minutes=45),
        deadline=listing.safe_until,
    )

    nn_route = nearest_neighbor_route(volunteer.location, now, [p_stop, d_stop])
    opt_route, dist, dur = two_opt_optimize(volunteer.location, now, nn_route)
    assert len(opt_route) == 2
    assert opt_route[0].stop_type == "pickup"
    assert opt_route[1].stop_type == "delivery"

    # 7. Handover Checkpoint and Delivery Completion
    bus.publish(
        "pickup.completed",
        {
            "listing_id": listing.id,
            "donor_id": donor.uid,
            "ngo_id": ngo.uid,
            "quantity_kg": 40.0,
            "portions": 120,
            "temperature_celsius": 68.5,
        },
    )

    # 8. Verify Impact Metrics & CSR Certificate
    global_impact = impact_calc.get_global_metrics()
    assert global_impact["total_kg_diverted"] == 40.0
    assert global_impact["total_meals_saved"] == 120
    assert global_impact["total_co2e_avoided_kg"] == 100.0  # 40 * 2.5

    donor_impact = impact_calc.get_donor_metrics(donor.uid)
    assert donor_impact["total_kg_diverted"] == 40.0

    # 9. Generate Certificate PDF
    cert_pdf = generate_csr_certificate_pdf(
        donor_id=donor.uid,
        donor_name=donor.name,
        metrics=donor_impact,
        month_year="October 2026",
    )
    assert cert_pdf.startswith(b"%PDF")
    assert len(cert_pdf) > 2000

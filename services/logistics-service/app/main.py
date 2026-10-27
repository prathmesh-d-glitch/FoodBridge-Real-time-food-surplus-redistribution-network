import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from shared.config import settings
from shared.events import EventMessage, get_event_bus
from shared.firestore_client import get_firestore_client
from shared.logging_setup import set_correlation_id, setup_logger
from shared.models import GeoPoint, RouteStop
from app.routes import router

logger = setup_logger("logistics_service")


from typing import Any, Dict, Optional
from app.route_optimizer import nearest_neighbor_route, two_opt_optimize
from shared.models import GeoPoint, RouteStatus, RouteStop, VolunteerRoute


def process_offer_accepted(data: Dict[str, Any], bus, db) -> Optional[VolunteerRoute]:
    """When an NGO accepts an offer, automatically assemble pickup & delivery stops,
    optimize the volunteer itinerary via Nearest-Neighbour + 2-Opt TSP, and assign the route.
    """
    listing_id = data.get("listing_id")
    donor_id = data.get("donor_id")
    ngo_id = data.get("ngo_id")

    if not listing_id:
        return None

    listing_doc = db.get_document("listings", listing_id) or {}
    ngo_doc = db.get_document("users", ngo_id) or {}

    donor_loc = listing_doc.get("location", {"latitude": 12.9716, "longitude": 77.5946, "address": "Donor Location"})
    ngo_loc = ngo_doc.get("location", {"latitude": 12.9784, "longitude": 77.6408, "address": "NGO Shelter"})

    now = datetime.now(timezone.utc)
    safe_until_str = listing_doc.get("safe_until")
    deadline = (
        datetime.fromisoformat(safe_until_str)
        if safe_until_str
        else now + timedelta(hours=3)
    )

    donor_name = listing_doc.get("donor_name") or "Donor Facility"
    ngo_name = ngo_doc.get("name") or "NGO Relief Shelter"

    pickup_stop = RouteStop(
        stop_id=f"stop_pick_{uuid.uuid4().hex[:6]}",
        stop_type="pickup",
        listing_id=listing_id,
        target_name=donor_name,
        location=GeoPoint(**donor_loc),
        estimated_arrival=now + timedelta(minutes=20),
        deadline=deadline - timedelta(minutes=settings.SAFETY_MARGIN_MINUTES),
        completed=False,
    )

    delivery_stop = RouteStop(
        stop_id=f"stop_del_{uuid.uuid4().hex[:6]}",
        stop_type="delivery",
        listing_id=listing_id,
        target_name=ngo_name,
        location=GeoPoint(**ngo_loc),
        estimated_arrival=now + timedelta(minutes=45),
        deadline=deadline,
        completed=False,
    )

    # Store stops in queue
    db.set_document("pending_stops", pickup_stop.stop_id, pickup_stop.model_dump(mode="json"))
    db.set_document("pending_stops", delivery_stop.stop_id, delivery_stop.model_dump(mode="json"))
    logger.info(f"Generated route stops for listing {listing_id} following offer acceptance")

    # Select primary or available volunteer courier
    volunteers = db.query_collection("users", filters=[("role", "==", "volunteer")])
    vol_id = "vol_arun_kumar"
    vol_name = "Arun Kumar"
    if volunteers:
        vol_id = volunteers[0].get("uid", "vol_arun_kumar")
        vol_name = volunteers[0].get("name", "Arun Kumar")

    start_pos = GeoPoint(latitude=12.9700, longitude=77.5900, address="Cubbon Park Courier Hub")
    stops = [pickup_stop, delivery_stop]

    nn_stops = nearest_neighbor_route(start_pos, now, stops)
    opt_stops, dist, dur = two_opt_optimize(start_pos, now, nn_stops)

    route_id = f"rt_{uuid.uuid4().hex[:10]}"
    new_route = VolunteerRoute(
        id=route_id,
        volunteer_id=vol_id,
        volunteer_name=vol_name,
        stops=opt_stops,
        total_distance_km=dist,
        estimated_duration_mins=dur,
        status=RouteStatus.ASSIGNED,
    )
    db.set_document("routes", new_route.id, new_route.model_dump(mode="json"))
    logger.info(f"Auto-assigned optimized route {route_id} to volunteer {vol_name} ({vol_id}) for {donor_name} -> {ngo_name}")

    # Emit route.assigned event for notification dispatch
    bus.publish(
        topic="route.assigned",
        data={
            "route_id": route_id,
            "volunteer_id": vol_id,
            "volunteer_name": vol_name,
            "listing_id": listing_id,
            "donor_name": donor_name,
            "ngo_name": ngo_name,
            "stops_count": 2,
            "total_distance_km": dist,
        },
    )
    return new_route


@asynccontextmanager
async def lifespan(app: FastAPI):
    bus = get_event_bus()
    db = get_firestore_client()

    def _handle_offer_accepted(msg: EventMessage):
        process_offer_accepted(msg.data, bus, db)

    bus.subscribe("offer.accepted", _handle_offer_accepted)
    logger.info("Logistics service event listeners registered for offer.accepted")
    yield


app = FastAPI(
    title="FoodBridge Logistics Service",
    description="Volunteer route optimization (Nearest-Neighbour + 2-Opt TSP) and verified handovers",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    cid = request.headers.get("x-correlation-id") or str(uuid.uuid4())
    set_correlation_id(cid)
    response = await call_next(request)
    response.headers["x-correlation-id"] = cid
    return response


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "logistics-service",
        "environment": settings.ENVIRONMENT,
    }


@app.post("/events/offer-accepted", status_code=202)
def event_offer_accepted(payload: Dict[str, Any]):
    """Pub/Sub push subscription endpoint for offer.accepted events."""
    data = payload.get("data", payload)
    route = process_offer_accepted(data, get_event_bus(), get_firestore_client())
    return {"status": "dispatched", "route_id": route.id if route else None}


app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.LOGISTICS_SERVICE_PORT, reload=True)

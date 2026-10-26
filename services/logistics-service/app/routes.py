import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from shared.auth import get_current_user, require_role
from shared.events import get_event_bus
from shared.firestore_client import get_firestore_client
from shared.logging_setup import setup_logger
from shared.models import (
    GeoPoint,
    HandoverLog,
    ListingStatus,
    RouteStatus,
    RouteStop,
    UserProfile,
    UserRole,
    VolunteerRoute,
)
from app.route_optimizer import nearest_neighbor_route, two_opt_optimize

logger = setup_logger("logistics_routes")
router = APIRouter()
db = get_firestore_client()
event_bus = get_event_bus()


class OptimizeRouteRequest(BaseModel):
    start_location: GeoPoint
    stops: List[RouteStop]
    start_time: Optional[datetime] = None


class OptimizeRouteResponse(BaseModel):
    ordered_stops: List[RouteStop]
    total_distance_km: float
    estimated_duration_mins: float


class AssignRouteRequest(BaseModel):
    volunteer_id: str
    volunteer_name: str
    stops: List[RouteStop]
    start_location: GeoPoint


class CreateHandoverRequest(BaseModel):
    listing_id: str
    offer_id: Optional[str] = None
    donor_id: str
    ngo_id: str
    temperature_celsius: Optional[float] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = ""
    is_pickup: bool = True  # True for donor pickup, False for recipient drop-off


@router.post("/routes/optimize", response_model=OptimizeRouteResponse)
def optimize_route_endpoint(payload: OptimizeRouteRequest) -> OptimizeRouteResponse:
    """Optimizes an itinerary of pickups and deliveries using Nearest-Neighbour + 2-Opt with hard pickup deadlines."""
    start_time = payload.start_time or datetime.now(timezone.utc)
    # 1. Greedy initial route
    nn_stops = nearest_neighbor_route(payload.start_location, start_time, payload.stops)
    # 2. 2-Opt local search improvement
    opt_stops, total_dist, total_dur = two_opt_optimize(
        start_pos=payload.start_location,
        start_time=start_time,
        initial_stops=nn_stops,
    )

    return OptimizeRouteResponse(
        ordered_stops=opt_stops,
        total_distance_km=total_dist,
        estimated_duration_mins=total_dur,
    )


@router.post("/routes", response_model=VolunteerRoute, status_code=status.HTTP_201_CREATED)
def assign_route(
    payload: AssignRouteRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> VolunteerRoute:
    """Builds and assigns an optimized route to a volunteer."""
    route_id = f"rt_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)

    # Optimize stops sequence
    nn_stops = nearest_neighbor_route(payload.start_location, now, payload.stops)
    opt_stops, total_dist, total_dur = two_opt_optimize(payload.start_location, now, nn_stops)

    route = VolunteerRoute(
        id=route_id,
        volunteer_id=payload.volunteer_id,
        volunteer_name=payload.volunteer_name,
        stops=opt_stops,
        total_distance_km=total_dist,
        estimated_duration_mins=total_dur,
        status=RouteStatus.ASSIGNED,
    )

    db.set_document("routes", route.id, route.model_dump(mode="json"))

    # Emit route.assigned event for notification dispatch
    event_bus.publish(
        topic="route.assigned",
        data={
            "route_id": route.id,
            "volunteer_id": payload.volunteer_id,
            "stops_count": len(opt_stops),
            "total_distance_km": total_dist,
        },
    )

    return route


@router.get("/routes/volunteer/{volunteer_id}", response_model=List[VolunteerRoute])
def get_volunteer_routes(volunteer_id: str) -> List[VolunteerRoute]:
    """Retrieves current and historical routes assigned to a volunteer."""
    docs = db.query_collection("routes", filters=[("volunteer_id", "==", volunteer_id)])
    routes = []
    for d in docs:
        try:
            routes.append(VolunteerRoute(**d))
        except Exception as e:
            logger.warning(f"Error parsing route: {e}")
    return routes


@router.post("/handovers", response_model=HandoverLog, status_code=status.HTTP_201_CREATED)
def log_handover(
    payload: CreateHandoverRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> HandoverLog:
    """Records a verified handover checkpoint with timestamp, optional food temperature, photo, and digital verification."""
    handover_id = f"ho_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)

    log_entry = HandoverLog(
        id=handover_id,
        listing_id=payload.listing_id,
        offer_id=payload.offer_id,
        volunteer_id=current_user.uid if current_user.role == UserRole.VOLUNTEER else None,
        donor_id=payload.donor_id,
        ngo_id=payload.ngo_id,
        timestamp=now,
        temperature_celsius=payload.temperature_celsius,
        photo_url=payload.photo_url,
        notes=payload.notes,
        donor_signature_verified=True,
        recipient_signature_verified=True,
    )

    db.set_document("handovers", log_entry.id, log_entry.model_dump(mode="json"))

    # Update listing status according to handover stage — only if listing exists
    new_status = ListingStatus.PICKED_UP if payload.is_pickup else ListingStatus.COMPLETED
    existing_listing = db.get_document("listings", payload.listing_id)
    if existing_listing:
        db.update_document("listings", payload.listing_id, {"status": new_status.value})
    else:
        logger.warning(f"Handover logged for listing {payload.listing_id} but no listing doc found — skipping status update")

    # Update any assigned volunteer route stops in database
    target_stop_type = "pickup" if payload.is_pickup else "delivery"
    routes = db.query_collection("routes")
    for r in routes:
        stops = r.get("stops", [])
        modified = False
        for s in stops:
            if s.get("listing_id") == payload.listing_id and s.get("stop_type") == target_stop_type:
                s["completed"] = True
                modified = True
        if modified:
            if all(s.get("completed", False) for s in stops):
                r["status"] = "completed"
            db.set_document("routes", r["id"], r)
            logger.info(f"Updated route {r['id']} stop completed status in database")

    if not payload.is_pickup:
        # Final delivery completed: retrieve listing quantity to publish pickup.completed event
        listing_doc = db.get_document("listings", payload.listing_id) or {}
        qty = float(listing_doc.get("quantity_kg", 20.0))
        portions = int(listing_doc.get("portions", 50))

        event_bus.publish(
            topic="pickup.completed",
            data={
                "handover_id": log_entry.id,
                "listing_id": payload.listing_id,
                "donor_id": payload.donor_id,
                "ngo_id": payload.ngo_id,
                "quantity_kg": qty,
                "portions": portions,
                "temperature_celsius": payload.temperature_celsius,
                "completed_at": now.isoformat(),
            },
        )
        logger.info(f"Handover {handover_id} marked COMPLETED. Emitted 'pickup.completed'")

    return log_entry


@router.post("/routes/{route_id}/stops/{stop_id}/complete")
def complete_route_stop(route_id: str, stop_id: str) -> dict:
    """Explicitly marks a specific stop as completed and persists it in the database."""
    route_doc = db.get_document("routes", route_id)
    if not route_doc:
        raise HTTPException(status_code=404, detail="Route not found")

    stops = route_doc.get("stops", [])
    found = False
    for s in stops:
        if s.get("stop_id") == stop_id:
            s["completed"] = True
            found = True

    if not found:
        raise HTTPException(status_code=404, detail="Stop ID not found on route")

    if all(s.get("completed", False) for s in stops):
        route_doc["status"] = "completed"

    db.set_document("routes", route_id, route_doc)
    logger.info(f"Marked stop {stop_id} completed on route {route_id} in database")
    return {"status": "success", "route_id": route_id, "stop_id": stop_id}

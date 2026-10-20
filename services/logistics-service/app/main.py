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


@asynccontextmanager
async def lifespan(app: FastAPI):
    bus = get_event_bus()
    db = get_firestore_client()

    def _handle_offer_accepted(msg: EventMessage):
        """When an NGO accepts an offer, automatically assemble pickup & delivery stops."""
        listing_id = msg.data.get("listing_id")
        donor_id = msg.data.get("donor_id")
        ngo_id = msg.data.get("ngo_id")

        if not listing_id:
            return

        listing_doc = db.get_document("listings", listing_id) or {}
        ngo_doc = db.get_document("users", ngo_id) or {}

        donor_loc = listing_doc.get("location", {"latitude": 12.9716, "longitude": 77.5946})
        ngo_loc = ngo_doc.get("location", {"latitude": 12.9784, "longitude": 77.6408})

        now = datetime.now(timezone.utc)
        safe_until_str = listing_doc.get("safe_until")
        deadline = (
            datetime.fromisoformat(safe_until_str)
            if safe_until_str
            else now + timedelta(hours=3)
        )

        pickup_stop = RouteStop(
            stop_id=f"stop_pick_{uuid.uuid4().hex[:6]}",
            stop_type="pickup",
            listing_id=listing_id,
            target_name=listing_doc.get("donor_name", "Donor Location"),
            location=GeoPoint(**donor_loc),
            estimated_arrival=now + timedelta(minutes=20),
            deadline=deadline - timedelta(minutes=settings.SAFETY_MARGIN_MINUTES),
        )

        delivery_stop = RouteStop(
            stop_id=f"stop_del_{uuid.uuid4().hex[:6]}",
            stop_type="delivery",
            listing_id=listing_id,
            target_name=ngo_doc.get("name", "NGO Shelter"),
            location=GeoPoint(**ngo_loc),
            estimated_arrival=now + timedelta(minutes=45),
            deadline=deadline,
        )

        # Store pending assignment in stops queue
        db.set_document("pending_stops", pickup_stop.stop_id, pickup_stop.model_dump(mode="json"))
        db.set_document("pending_stops", delivery_stop.stop_id, delivery_stop.model_dump(mode="json"))
        logger.info(f"Generated route stops for listing {listing_id} following offer acceptance")

    bus.subscribe("offer.accepted", _handle_offer_accepted)
    logger.info("Logistics service event listeners registered")
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


app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.LOGISTICS_SERVICE_PORT, reload=True)

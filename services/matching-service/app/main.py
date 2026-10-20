import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from shared.config import settings
from shared.events import EventMessage, get_event_bus
from shared.logging_setup import set_correlation_id, setup_logger
from app.cascade import CascadeManager
from app.routes import router
from app.tasks import handle_offer_timeout

logger = setup_logger("matching_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Register asynchronous event bus subscriptions
    bus = get_event_bus()

    def _on_listing_created(msg: EventMessage):
        listing_id = msg.data.get("listing_id")
        if listing_id:
            logger.info(f"Received listing.created for {listing_id}")
            CascadeManager().process_new_listing(listing_id)

    def _on_offer_timeout(msg: EventMessage):
        offer_id = msg.data.get("offer_id")
        listing_id = msg.data.get("listing_id")
        rank = msg.data.get("rank", 1)
        if offer_id and listing_id:
            handle_offer_timeout(offer_id, listing_id, rank)

    bus.subscribe("listing.created", _on_listing_created)
    bus.subscribe("offer.timeout", _on_offer_timeout)
    logger.info("Matching service event subscriptions initialized")
    yield


app = FastAPI(
    title="FoodBridge Matching Service",
    description="Real-time spoilage-aware composite matching and cascading offers",
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
        "service": "matching-service",
        "environment": settings.ENVIRONMENT,
        "event_bus": settings.EVENT_BUS_TYPE,
    }


app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.MATCHING_SERVICE_PORT, reload=True)

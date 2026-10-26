import os
import sys
from pathlib import Path

# Ensure services/listing-service and services/shared are available on sys.path
_service_dir = Path(__file__).resolve().parent.parent
_shared_dir = _service_dir.parent / "shared"
if str(_service_dir) not in sys.path:
    sys.path.insert(0, str(_service_dir))
if str(_shared_dir) not in sys.path:
    sys.path.insert(0, str(_shared_dir))

import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from shared.config import settings
from shared.logging_setup import set_correlation_id, setup_logger

from app.routes import router
from app.admin_routes import router as admin_router

logger = setup_logger("listing_service")

app = FastAPI(
    title="FoodBridge Listing Service",
    description="Surplus food listing management with Gemini photo analysis and spoilage calculations",
    version="1.0.0",
)

# Enable CORS for frontend PWA
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
        "service": "listing-service",
        "environment": settings.ENVIRONMENT,
        "event_bus": settings.EVENT_BUS_TYPE,
    }


app.include_router(router)
app.include_router(admin_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.LISTING_SERVICE_PORT, reload=True)

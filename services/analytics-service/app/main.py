import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from shared.config import settings
from shared.events import EventMessage, get_event_bus
from shared.firestore_client import get_firestore_client
from shared.logging_setup import set_correlation_id, setup_logger
from app.bq_sync import sync_record_to_bigquery
from app.certificate import generate_csr_certificate_pdf
from app.forecast import SurplusForecaster
from app.impact import ImpactCalculator

logger = setup_logger("analytics_service")
impact_calc = ImpactCalculator()
forecaster = SurplusForecaster()
db = get_firestore_client()


@asynccontextmanager
async def lifespan(app: FastAPI):
    bus = get_event_bus()

    def _handle_pickup_completed(msg: EventMessage):
        data = msg.data
        listing_id = data.get("listing_id")
        donor_id = data.get("donor_id")
        ngo_id = data.get("ngo_id")
        quantity_kg = float(data.get("quantity_kg", 20.0))
        portions = data.get("portions")

        rec = impact_calc.record_completed_pickup(
            listing_id=listing_id,
            donor_id=donor_id,
            ngo_id=ngo_id,
            quantity_kg=quantity_kg,
            portions=portions,
        )

        # Sync to BigQuery table
        sync_record_to_bigquery("impact_records", [rec.model_dump(mode="json")])

    bus.subscribe("pickup.completed", _handle_pickup_completed)
    logger.info("Analytics event listeners registered for 'pickup.completed'")
    yield


app = FastAPI(
    title="FoodBridge Analytics Service",
    description="Impact metrics, CO2e telemetry, surplus forecasting, and CSR certificate generation",
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


@app.post("/events/pickup-completed")
def handle_pickup_completed_event(payload: Dict[str, Any]):
    data = payload.get("data", payload)
    listing_id = data.get("listing_id")
    donor_id = data.get("donor_id", "donor_taj_palace")
    ngo_id = data.get("ngo_id", "ngo_robin_hood")
    quantity_kg = float(data.get("quantity_kg", 20.0))
    portions = data.get("portions")

    rec = impact_calc.record_completed_pickup(
        listing_id=listing_id,
        donor_id=donor_id,
        ngo_id=ngo_id,
        quantity_kg=quantity_kg,
        portions=portions,
    )
    return {"status": "recorded", "impact_record_id": rec.id}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "analytics-service",
        "co2e_factor": settings.CO2E_FACTOR_KG_PER_KG,
    }


@app.get("/analytics/impact")
def get_platform_impact():
    """Retrieve live global impact metrics (meals saved, kg diverted, CO2e avoided)."""
    return impact_calc.get_global_metrics()


@app.get("/analytics/donor/{donor_id}")
def get_donor_impact(donor_id: str):
    """Retrieve donor-specific impact totals."""
    return impact_calc.get_donor_metrics(donor_id)


@app.get("/analytics/forecast")
def get_surplus_forecast(
    donor_id: Optional[str] = Query(None, description="Donor ID or omit for aggregate"),
    weekday: int = Query(4, ge=0, le=6, description="Target weekday (0=Mon, 6=Sun)"),
    hour: int = Query(22, ge=0, le=23, description="Target hour (0-23)"),
):
    """Predicts expected food surplus volume using seasonal-average baseline plus trend."""
    return forecaster.forecast_surplus(donor_id=donor_id, target_weekday=weekday, target_hour=hour)


@app.get("/analytics/certificate/{donor_id}")
def download_csr_certificate(donor_id: str, month: Optional[str] = "October 2026"):
    """Generates and serves a downloadable PDF Corporate Social Responsibility (CSR) certificate."""
    metrics = impact_calc.get_donor_metrics(donor_id)

    # Fetch donor name
    user_doc = db.get_document("users", donor_id)
    donor_name = user_doc.get("name", "Corporate Food Partner") if user_doc else "Corporate Food Partner"

    pdf_bytes = generate_csr_certificate_pdf(
        donor_id=donor_id,
        donor_name=donor_name,
        metrics=metrics,
        month_year=month or "October 2026",
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="FoodBridge_CSR_Certificate_{donor_id}.pdf"'
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.ANALYTICS_SERVICE_PORT, reload=True)

import pytest
from shared.firestore_client import InMemoryFirestoreClient, get_firestore_client
from app.certificate import generate_csr_certificate_pdf
from app.forecast import SurplusForecaster
from app.impact import ImpactCalculator


@pytest.fixture(autouse=True)
def clean_db():
    db = get_firestore_client()
    if isinstance(db, InMemoryFirestoreClient):
        db.clear()


def test_impact_calculation():
    calc = ImpactCalculator()

    # Record 40 kg with 100 portions
    rec = calc.record_completed_pickup(
        listing_id="list_1",
        donor_id="donor_caterer_1",
        ngo_id="ngo_1",
        quantity_kg=40.0,
        portions=100,
    )

    assert rec.quantity_kg == 40.0
    assert rec.meals_saved == 100
    # CO2e avoided = 40 * 2.5 = 100 kg
    assert rec.co2e_avoided_kg == 100.0

    global_metrics = calc.get_global_metrics()
    assert global_metrics["total_kg_diverted"] == 40.0
    assert global_metrics["total_meals_saved"] == 100
    assert global_metrics["total_co2e_avoided_kg"] == 100.0
    assert global_metrics["completed_deliveries"] == 1


def test_surplus_forecasting():
    forecaster = SurplusForecaster()
    # Forecast Friday 22:00 (banquet rush)
    forecast = forecaster.forecast_surplus(target_weekday=4, target_hour=22)

    assert forecast["weekday"] == 4
    assert forecast["hour"] == 22
    assert forecast["predicted_surplus_kg"] > 0.0
    assert forecast["expected_portions"] > 0
    assert forecast["confidence_score"] > 0.5


def test_csr_certificate_pdf_generation():
    metrics = {
        "total_kg_diverted": 250.5,
        "total_meals_saved": 715,
        "total_co2e_avoided_kg": 626.25,
    }
    pdf_bytes = generate_csr_certificate_pdf(
        donor_id="donor_taj_palace",
        donor_name="Taj Palace Luxury Catering",
        metrics=metrics,
        month_year="October 2026",
    )

    assert pdf_bytes is not None
    # Valid PDF magic bytes
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000

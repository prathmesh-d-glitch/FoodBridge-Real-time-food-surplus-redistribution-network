# FoodBridge: Complete Microservices REST API Reference

This document provides request and response specifications for all FoodBridge microservices. All endpoints support standard HTTP response codes, structured JSON error bodies, and correlation ID tracking via the `X-Correlation-ID` header.

---

## 1. Listing Service (Port 8001 / `foodbridge-listing-service`)

### 1.1. Create Food Surplus Listing
- **Endpoint**: `POST /api/listings`
- **Auth**: Bearer Token (`roles: ["donor", "admin"]`)
- **Description**: Submits a surplus food listing. Automatically runs Gemini multimodal image analysis, determines safe consumption shelf life (`safe_until`), indexes geohash, and publishes `listing.created` to Cloud Pub/Sub.

**Request Body**:
```json
{
  "donor_id": "usr_donor_taj_01",
  "donor_name": "Taj West End Kitchens",
  "category": "Cooked Meals",
  "dietary_type": "Veg",
  "portions": 85,
  "weight_kg": 34.0,
  "storage_condition": "Hot-Hold (>60C)",
  "prepared_at": "2026-10-23T12:30:00Z",
  "latitude": 12.9866,
  "longitude": 77.5855,
  "photo_url": "https://storage.googleapis.com/foodbridge-photos/taj_meals_85.jpg"
}
```

**Response (201 Created)**:
```json
{
  "id": "list_9a8f21bc",
  "donor_id": "usr_donor_taj_01",
  "donor_name": "Taj West End Kitchens",
  "category": "Cooked Meals",
  "dietary_type": "Veg",
  "portions": 85,
  "weight_kg": 34.0,
  "storage_condition": "Hot-Hold (>60C)",
  "prepared_at": "2026-10-23T12:30:00Z",
  "safe_until": "2026-10-23T16:30:00Z",
  "remaining_shelf_life_hours": 4.0,
  "geohash": "tdr1v4",
  "status": "AVAILABLE",
  "created_at": "2026-10-23T12:35:10Z",
  "ai_analysis": {
    "food_type": "Fresh Cooked Rice and Lentil Curry",
    "suggested_portions": 85,
    "confidence": 0.94,
    "safety_flags": [],
    "model_used": "gemini-1.5-flash"
  }
}
```

---

### 1.2. Multimodal AI Photo Analysis
- **Endpoint**: `POST /api/listings/analyze-photo`
- **Auth**: Bearer Token (`roles: ["donor", "admin"]`)
- **Description**: Pre-upload inspection endpoint. Runs Gemini 1.5 Flash image inspection for portion validation and food hygiene checks.

**Request Body**:
```json
{
  "photo_url": "https://storage.googleapis.com/foodbridge-photos/buffet_trays_temp.jpg",
  "declared_category": "Cooked Meals"
}
```

**Response (200 OK)**:
```json
{
  "food_type": "Vegetable Biryani & Sambar in stainless steel chafing dishes",
  "estimated_portions": 90,
  "estimated_shelf_life_hours": 4.0,
  "safety_flags": [],
  "confidence": 0.92,
  "model_used": "gemini-1.5-flash"
}
```

---

## 2. Matching Service (Port 8002 / `foodbridge-matching-service`)

### 2.1. Accept Cascading Offer
- **Endpoint**: `POST /api/offers/{offer_id}/accept`
- **Auth**: Bearer Token (`roles: ["ngo", "admin"]`)
- **Description**: Recipient NGO accepts the offered food. Performs atomic transition from `OFFERED` to `ACCEPTED`, transitions the listing to `MATCHED`, and publishes `offer.accepted` to assign volunteer logistics.

**Response (200 OK)**:
```json
{
  "offer_id": "off_7c2b81d9",
  "listing_id": "list_9a8f21bc",
  "recipient_id": "usr_ngo_asha_01",
  "status": "ACCEPTED",
  "responded_at": "2026-10-23T12:40:15Z",
  "message": "Offer accepted successfully. Logistics routing initiated."
}
```

---

### 2.2. Decline Cascading Offer & Auto-Escalate
- **Endpoint**: `POST /api/offers/{offer_id}/decline`
- **Auth**: Bearer Token (`roles: ["ngo", "admin"]`)
- **Description**: Recipient declines. Cancels current offer and immediately escalates to Rank 2 candidate via Pub/Sub.

**Request Body**:
```json
{
  "reason": "Kitchen at full capacity for lunch service"
}
```

**Response (200 OK)**:
```json
{
  "offer_id": "off_7c2b81d9",
  "status": "DECLINED",
  "escalated": true,
  "next_rank_offered": 2,
  "message": "Offer declined. Cascaded to next eligible recipient."
}
```

---

### 2.3. Query Live Offers with Explainability
- **Endpoint**: `GET /api/offers?recipient_id=usr_ngo_asha_01&status=OFFERED`
- **Auth**: Bearer Token (`roles: ["ngo", "volunteer", "admin"]`)
- **Description**: Returns active offers with full mathematical score explainability breakdown.

**Response (200 OK)**:
```json
[
  {
    "id": "off_7c2b81d9",
    "listing_id": "list_9a8f21bc",
    "recipient_id": "usr_ngo_asha_01",
    "composite_score": 0.865,
    "score_breakdown": {
      "time_feasibility": 0.817,
      "proximity": 0.767,
      "capacity_fit": 1.000,
      "dietary_match": 1.000,
      "reliability": 0.920,
      "need_urgency": 0.900
    },
    "expires_at": "2026-10-23T12:48:00Z",
    "timeout_seconds": 480,
    "status": "OFFERED"
  }
]
```

---

## 3. Logistics Service (Port 8004 / `foodbridge-logistics-service`)

### 3.1. Fetch Active 2-Opt Volunteer Route
- **Endpoint**: `GET /api/logistics/routes/active?volunteer_id=usr_vol_kiran_01`
- **Auth**: Bearer Token (`roles: ["volunteer", "admin"]`)
- **Description**: Returns ordered stops calculated by the 2-Opt TSP algorithm respecting strict pickup deadlines.

**Response (200 OK)**:
```json
{
  "route_id": "rt_84ef011a",
  "volunteer_id": "usr_vol_kiran_01",
  "total_distance_km": 6.8,
  "estimated_duration_min": 28.5,
  "stops": [
    {
      "sequence": 1,
      "type": "PICKUP",
      "location_name": "Taj West End Kitchens",
      "address": "Race Course Rd, High Grounds, Bengaluru",
      "latitude": 12.9866,
      "longitude": 77.5855,
      "deadline": "2026-10-23T13:30:00Z",
      "portions": 85,
      "estimated_arrival": "2026-10-23T12:55:00Z"
    },
    {
      "sequence": 2,
      "type": "DROPOFF",
      "location_name": "Asha Shelter Home",
      "address": "Vasanth Nagar, Bengaluru",
      "latitude": 12.9902,
      "longitude": 77.5898,
      "deadline": "2026-10-23T14:30:00Z",
      "portions": 85,
      "estimated_arrival": "2026-10-23T13:12:00Z"
    }
  ]
}
```

---

### 3.2. Record Food Handover Checkpoint
- **Endpoint**: `POST /api/logistics/handover/pickup`
- **Auth**: Bearer Token (`roles: ["volunteer", "admin"]`)

**Request Body**:
```json
{
  "listing_id": "list_9a8f21bc",
  "volunteer_id": "usr_vol_kiran_01",
  "measured_temp_celsius": 68.5,
  "photo_proof_url": "https://storage.googleapis.com/foodbridge-handover/pickup_9a8f.jpg",
  "notes": "Food sealed in thermal insulated transport containers."
}
```

**Response (200 OK)**:
```json
{
  "status": "RECORDED",
  "checkpoint": "PICKUP_COMPLETE",
  "timestamp": "2026-10-23T12:57:42Z",
  "safety_verdict": "COMPLIANT_HOT_HOLD"
}
```

---

## 4. Analytics Service (Port 8005 / `foodbridge-analytics-service`)

### 4.1. Live Impact Metrics
- **Endpoint**: `GET /api/analytics/impact`
- **Auth**: Public / No auth required
- **Description**: Returns network-wide sustainability metrics calculated with EPA / FoodBridge conversion factors.

**Response (200 OK)**:
```json
{
  "total_meals_saved": 4850,
  "total_kg_diverted": 1940.0,
  "total_co2e_avoided_kg": 4850.0,
  "total_donations_completed": 128,
  "active_donors_count": 42,
  "active_ngos_count": 67,
  "active_volunteers_count": 89,
  "co2e_factor_kg_per_kg_food": 2.5
}
```

---

### 4.2. Surplus Forecasting by Donor & Diurnal Curve
- **Endpoint**: `GET /api/analytics/forecast?donor_id=usr_donor_taj_01&weekday=5`
- **Auth**: Bearer Token (`roles: ["donor", "admin"]`)

**Response (200 OK)**:
```json
{
  "donor_id": "usr_donor_taj_01",
  "weekday": 5,
  "methodology": "Seasonal baseline moving average + 3-week linear trend + diurnal meal multipliers",
  "forecast_hourly": [
    { "hour": 14, "expected_portions": 78.5, "confidence_interval": [65.0, 92.0] },
    { "hour": 15, "expected_portions": 32.0, "confidence_interval": [20.0, 44.0] },
    { "hour": 22, "expected_portions": 115.0, "confidence_interval": [95.0, 135.0] }
  ]
}
```

---

### 4.3. Download Cryptographic CSR Certificate (PDF)
- **Endpoint**: `GET /api/analytics/certificate/{donor_id}?month=10&year=2026`
- **Auth**: Bearer Token (`roles: ["donor", "admin"]`)
- **Description**: Returns binary PDF (`application/pdf`) with corporate sustainability summary and SHA-256 integrity hash.

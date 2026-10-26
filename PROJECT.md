# FoodBridge — Project Documentation

> **Real-Time Food Surplus Redistribution Platform**  
> Cloud Computing Project | Full-Stack Microservices · PWA · AI-Powered Matching

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Microservices](#4-microservices)
5. [Frontend (PWA)](#5-frontend-pwa)
6. [Data Models & Persistence](#6-data-models--persistence)
7. [Core Features](#7-core-features)
8. [AI & Algorithms](#8-ai--algorithms)
9. [Authentication & Roles](#9-authentication--roles)
10. [Internationalisation (i18n)](#10-internationalisation-i18n)
11. [Event-Driven Architecture](#11-event-driven-architecture)
12. [Deployment](#12-deployment)
13. [Local Development Setup](#13-local-development-setup)

---

## 1. Project Overview

FoodBridge is a **cloud-native microservices platform** that connects food donors (restaurants, caterers, hotels) with NGO shelters and volunteer drivers to redistribute surplus food before it spoils. The system uses real-time spoilage-aware scoring, Gemini AI photo analysis, geospatial matching, and route optimisation to maximise food rescue efficiency.

### Problem Statement
India wastes ~70 million tonnes of food annually while 190 million people go hungry. Existing redistribution efforts fail because:
- No real-time visibility of surplus availability
- Manual matching is too slow vs. food safety windows
- No logistics coordination for last-mile pickup

### Solution
FoodBridge automates the entire pipeline: **Donor posts → AI analyses → Engine matches → Volunteer routes → Impact recorded** — all within the food's safe consumption window.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     React PWA (Vite + TypeScript)                │
│          Donor · NGO · Volunteer · Impact · Admin · Map          │
└────────────────────────┬────────────────────────────────────────┘
                         │  REST / CORS
         ┌───────────────┼───────────────────────────────┐
         │               │                               │
   ┌─────▼──────┐  ┌─────▼──────┐  ┌────────────┐  ┌────▼───────┐
   │  Listing   │  │  Matching  │  │ Logistics  │  │ Analytics  │
   │  Service   │  │  Service   │  │  Service   │  │  Service   │
   │  :8001     │  │  :8002     │  │  :8004     │  │  :8005     │
   └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └────┬───────┘
         │               │               │               │
         └───────────────┴───────┬───────┴───────────────┘
                                 │ In-process Event Bus
                   ┌─────────────┼─────────────┐
             ┌─────▼─────┐ ┌────▼─────┐ ┌─────▼──────┐
             │Notification│ │  Expiry  │ │  Shared    │
             │  Service  │ │   Job    │ │  Library   │
             │  :8003    │ │  :8006   │ │ (models,   │
             └────────────┘ └──────────┘ │  geo, auth)│
                                         └────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   .foodbridge_db.json    │
                    │  (File-backed persistent │
                    │   store — swap with      │
                    │   Firestore for prod)    │
                    └─────────────────────────┘
```

### Key Design Decisions
| Decision | Rationale |
|---|---|
| Microservices | Independent scaling, clear bounded contexts |
| File-backed DB (dev) | Zero credentials; swappable with Cloud Firestore |
| In-process event bus | Works locally; same interface as Pub/Sub in prod |
| PWA (not native app) | Cross-platform, installable, offline-capable |
| Vite + TypeScript | Fast dev, type-safe API contracts |

---

## 3. Technology Stack

### Backend
| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI (async, auto-docs) |
| Data Validation | Pydantic v2 |
| Persistence (dev) | JSON file (`PersistentInMemoryFirestoreClient`) |
| Persistence (prod) | Google Cloud Firestore |
| Auth | Firebase Auth tokens + Bearer headers |
| Events (dev) | In-process publish/subscribe bus |
| Events (prod) | Google Cloud Pub/Sub |
| AI | Google Gemini 1.5 Flash (vision & photo analysis) |
| PDF Generation | ReportLab |
| Geo | Pygeohash + Haversine distance |
| Analytics sink | BigQuery (prod), local file (dev) |

### Frontend
| Component | Technology |
|---|---|
| Framework | React 18 + TypeScript |
| Bundler | Vite |
| Maps | Leaflet.js + OpenStreetMap |
| Icons | Lucide React |
| Styling | Vanilla CSS (CSS variables, glassmorphism) |
| i18n | Custom React Context (EN / HI / KN) |
| Auth | Firebase Auth (email/password) |
| PWA | Service Worker + Web App Manifest |

### Infrastructure
| Component | Technology |
|---|---|
| Containerisation | Docker + docker-compose |
| Cloud | Google Cloud Platform |
| Container Registry | Artifact Registry |
| Serverless option | Cloud Run |
| Analytics | BigQuery |
| Storage | Firebase Storage (photos) |
| CI/CD | GitHub Actions |

---

## 4. Microservices

### 4.1 Listing Service (`listing-service` · port 8001)

**Responsibility:** Create, read, update, and expire food surplus listings.

| Endpoint | Method | Description |
|---|---|---|
| `/listings` | POST | Create listing + Gemini AI photo analysis + spoilage calc |
| `/listings` | GET | Fetch all listings (filter by status, donor_id) |
| `/listings/{id}` | GET | Get single listing details |
| `/listings/{id}/status` | PATCH | Update listing status (offered, picked_up, completed) |
| `/listings/analyze-photo` | POST | Standalone Gemini food photo analysis |
| `/admin/verifications` | GET | Partner verification queue |
| `/admin/verifications/{id}/approve` | POST | Approve partner FSSAI registration |
| `/admin/verifications/{id}/reject` | POST | Reject partner registration |
| `/admin/escalations` | GET | Matching escalation alerts |
| `/admin/escalations/{id}/resolve` | POST | Mark escalation resolved |
| `/admin/health-telemetry` | GET | Live microservice health probes |
| `/health` | GET | Service health check |

**Key logic:**
- Spoilage-aware `safe_until` computed from `prepared_at` + food category + storage condition (FSSAI / Codex Alimentarius standards)
- Geohash (precision-6) encoded at creation for spatial range queries
- Publishes `listing.created` event → triggers matching engine

### 4.2 Matching Service (`matching-service` · port 8002)

**Responsibility:** Rank NGOs for each food listing using a composite scoring algorithm, manage offer lifecycle.

| Endpoint | Method | Description |
|---|---|---|
| `/offers/ngo/{ngo_id}` | GET | Get all offers for an NGO |
| `/offers/{id}/accept` | POST | NGO accepts offer → triggers logistics assignment |
| `/offers/{id}/decline` | POST | NGO declines (cascades to next ranked NGO) |
| `/health` | GET | Service health check |

**Matching Algorithm — Composite Score (6 factors):**
| Factor | Weight | Calculation |
|---|---|---|
| Time Feasibility | High | `is_delivery_feasible()` — ETA + 15min buffer vs. `safe_until - 30min` |
| Proximity | High | Haversine distance (km) → normalised score |
| Capacity Fit | Medium | NGO capacity vs. listing `quantity_kg` |
| Dietary Match | Medium | NGO dietary prefs vs. listing `dietary_type` |
| Reliability | Medium | NGO historical reliability score (0–1) |
| Need Urgency | Low | NGO current queue depth |

NGOs are ranked 1–N; offers sent in cascade order. If Rank 1 times out (600s), offer auto-escalates to Rank 2.

### 4.3 Notification Service (`notification-service` · port 8003)

**Responsibility:** Push notifications and in-app alerts on key lifecycle events.

Listens for events: `listing.created`, `match.offered`, `offer.accepted`, `pickup.completed`

### 4.4 Logistics Service (`logistics-service` · port 8004)

**Responsibility:** TSP route optimisation, volunteer assignment, handover verification.

| Endpoint | Method | Description |
|---|---|---|
| `/routes/optimize` | POST | Nearest-Neighbour + 2-Opt TSP optimisation |
| `/routes` | POST | Assign optimised route to volunteer |
| `/routes/volunteer/{id}` | GET | Get all routes for a volunteer |
| `/routes/{id}/stops/{stop_id}/complete` | POST | Mark a stop completed (persisted) |
| `/handovers` | POST | Log food handover with temp, notes, digital verification |
| `/health` | GET | Service health check |

**Route Optimisation Algorithm:**
1. **Nearest Neighbour heuristic** — greedy initial tour respecting hard pickup deadlines
2. **2-Opt local search** — iteratively swap edge pairs to reduce total distance
3. Output includes `total_distance_km` and `estimated_duration_mins`

**Handover Verification:**
- Records temperature (°C), notes, timestamp
- Sets `donor_signature_verified = True`, `recipient_signature_verified = True`
- Publishes `pickup.completed` event → Analytics records impact

### 4.5 Analytics Service (`analytics-service` · port 8005)

**Responsibility:** Impact metrics aggregation, CSR PDF certificate generation, surplus forecasting.

| Endpoint | Method | Description |
|---|---|---|
| `/analytics/impact` | GET | Global platform impact (meals, kg, CO2e) |
| `/analytics/donor/{donor_id}` | GET | Donor-specific impact totals |
| `/analytics/forecast` | GET | ML surplus forecast (weekday × hour) |
| `/analytics/certificate/{donor_id}` | GET | Download CSR PDF certificate |
| `/events/pickup-completed` | POST | Manual event trigger (for testing) |
| `/health` | GET | Service health check |

**CO2e Calculation:** `kg_food × 2.5 kg_CO2e/kg` (IPCC food waste emission factor)  
**Meals Calculation:** `kg_food × 2.8 meals/kg`

**Surplus Forecasting:** Seasonal baseline (weekday × hour cell averages) × trend multiplier. Outputs `predicted_surplus_kg`, `expected_portions`, `confidence_score`.

**CSR Certificate:** ReportLab PDF with QR code placeholder, impact metrics table, UN SDG 12.3 compliance badge, blockchain-verifiable hash header.

### 4.6 Expiry Job (`expiry-job` · port 8006)

**Responsibility:** Periodic scan of all `available` listings; marks expired ones (`safe_until < now`) as `expired` and publishes expiry events.

---

## 5. Frontend (PWA)

### Pages & Views

| Page | Route | Role Access | Description |
|---|---|---|---|
| Login | `#login` | Public | Firebase Auth email/password sign-in |
| Donor Dashboard | `#donor` | Donor, Admin | Active surplus postings with AI analysis cards |
| Post Surplus | `#post_surplus` | Donor | Multi-step form: details → photo → AI analysis → submit |
| NGO Feed | `#ngo` | NGO | Ranked offer feed with accept/decline actions |
| Volunteer Route | `#volunteer` | Volunteer | Live map + optimised stop itinerary + handover modal |
| Live Map | `#map` | Public | Leaflet map showing all active listings and NGO locations |
| Impact Dashboard | `#impact` | Public | Animated counters + CSR certificate + surplus forecaster |
| Admin Console | `#admin` | Admin | Microservice telemetry + verification queue + escalations |

### Key Components

| Component | Purpose |
|---|---|
| `Layout.tsx` | Top navbar with segmented nav, location pill, language selector, role switcher |
| `ListingCard.tsx` | Surplus food card with freshness clock, AI badge, match score |
| `OfferCard.tsx` | NGO offer card with composite score breakdown and accept/decline |
| `FreshnessClock.tsx` | Animated countdown clock showing time-to-expiry |
| `ImpactCounter.tsx` | Animated number counter with smooth roll-up animation |
| `MapView.tsx` | Leaflet map with custom markers, route polylines |
| `MatchExplainer.tsx` | Radar/bar chart explaining composite match score factors |
| `TrustBadge.tsx` | Verification status badge (FSSAI, verified, reliability score) |

### PWA Features
- Service Worker with cache-first strategy for static assets
- Offline fallback page
- Web App Manifest for installability
- Nginx-served with SPA routing (`try_files $uri /index.html`)

---

## 6. Data Models & Persistence

### Core Models (Pydantic)

#### `DonorListing`
```
id, donor_id, donor_name, title, description
category: FoodCategory (cooked_meals | bakery_bread | raw_produce | dairy | packaged_goods | desserts)
storage_condition: StorageCondition (hot_hold | ambient | chilled | frozen)
dietary_type: DietaryType (veg | non_veg | vegan | halal | jain | any)
quantity_kg, portions
prepared_at, safe_until  ← auto-calculated by spoilage engine
location: GeoPoint (lat, lng, address)
geohash  ← Precision-6 encoded for spatial queries
photo_url, photo_analysis: PhotoAnalysisResult
status: ListingStatus (available | offered | claimed | picked_up | completed | expired | cancelled)
```

#### `Offer`
```
id, listing_id, donor_id, ngo_id, ngo_name
rank, score, score_breakdown: MatchScoreBreakdown
status: OfferStatus (offered | accepted | declined | timeout | cancelled)
response_timeout_seconds, offered_at, expires_at
```

#### `VolunteerRoute`
```
id, volunteer_id, volunteer_name
stops: List[RouteStop] (stop_id, stop_type, listing_id, target_name, location, eta, deadline, completed)
total_distance_km, estimated_duration_mins
status: RouteStatus (assigned | in_transit | completed | cancelled)
```

#### `HandoverLog`
```
id, listing_id, volunteer_id, donor_id, ngo_id
timestamp, temperature_celsius, photo_url, notes
donor_signature_verified, recipient_signature_verified
```

#### `ImpactRecord`
```
id, listing_id, donor_id, ngo_id
quantity_kg, meals_saved, co2e_avoided_kg, timestamp
```

### Persistence Strategy

| Environment | Backend | Notes |
|---|---|---|
| Local dev | `PersistentInMemoryFirestoreClient` | `.foodbridge_db.json` file-backed, shared across all service processes |
| Production | `RealFirestoreClient` | Cloud Firestore, set `GOOGLE_APPLICATION_CREDENTIALS` or `FIRESTORE_EMULATOR_HOST` |

The `get_firestore_client()` factory auto-selects based on environment variables — **zero code change needed for deployment**.

### Spoilage Calculation Table (FSSAI / Codex Alimentarius)

| Category | Hot Hold | Ambient | Chilled | Frozen |
|---|---|---|---|---|
| Cooked Meals | 4h | 3h | 24h | 72h |
| Bakery/Bread | 6h | 36h | 48h | 168h |
| Raw Produce | 4h | 24h | 72h | 168h |
| Dairy | 2h | 3h | 12h | 48h |
| Packaged Goods | 6h | 72h | 120h | 240h |
| Desserts | 2h | 6h | 16h | 72h |

---

## 7. Core Features

### 7.1 Surplus Posting (Donor)
- Multi-step form: food details → storage info → location (GPS auto-detect) → photo upload → review
- Real-time **Gemini AI photo analysis** on upload (food type, estimated portions, shelf-life hint, safety flags)
- Spoilage-aware `safe_until` auto-computed; shown as countdown timer
- `listing.created` event published → matching engine instantly triggered

### 7.2 AI-Powered Matching (Matching Engine)
- Six-factor composite scoring per NGO candidate
- Hard time-feasibility filter (spoilage clock + travel ETA + 30min safety margin)
- Cascade offer sending (Rank 1 → timeout → Rank 2 → …)
- Escalation alerts if no responses found within 15 km

### 7.3 NGO Offer Feed
- Live ranked offer list sorted by composite score
- Each offer shows: food details, match score breakdown, AI safety flags, ETA, expiry countdown
- One-click Accept / Decline with reason

### 7.4 Volunteer Route Optimisation
- 2-Opt TSP with nearest-neighbour seeding
- Map view with colour-coded pickup (green) / delivery (blue) markers
- Route polyline visualisation
- Per-stop handover verification modal: temperature log, notes, digital signatures
- Checkpoint persistence (localStorage + backend) survives page refresh

### 7.5 Live Map
- Leaflet + OpenStreetMap showing all active listings and NGO locations
- Colour-coded markers: green = donor/available, blue = NGO, orange = in-transit
- Click markers for details popup

### 7.6 Impact Dashboard
- Animated rolling counters: Meals Saved, kg Diverted, CO2e Avoided, Rescues Completed
- UN SDG 2 and SDG 12 aligned metrics
- **CSR PDF Certificate** download (ReportLab, verifiable hash)
- **Surplus Forecaster**: predict food volume by weekday × hour with confidence score

### 7.7 Admin Console
- **Microservice Health Panel**: live latency + port + green/red status for all 6 services
- **Partner Verification Queue**: FSSAI license review with Approve/Reject (persisted to backend)
- **Matching Escalation Monitor**: active escalation alerts with Mark Resolved
- Auto-refreshes every 10 seconds

### 7.8 Language Switching (i18n)
- Three languages: English (EN), Hindi (HI), Kannada (KN)
- React Context (`LanguageProvider` + `useLanguage()`) — all pages re-render instantly
- Translation files cover all UI strings: navigation, buttons, labels, empty states, modals

---

## 8. AI & Algorithms

### Gemini 1.5 Flash — Food Photo Analysis
```
Input: photo (URL or base64) + food name hint
Output:
  - food_type: string
  - estimated_portions: int
  - shelf_life_hours_hint: float
  - safety_flags: list[str]  (e.g. "Hot holding verified above 65°C")
  - confidence: float (0–1)
  - source: "gemini" | "heuristic_fallback"
```
Falls back to category-based heuristics if Gemini API unavailable.

### Spoilage Engine
Based on FSSAI (Food Safety and Standards Authority of India) and Codex Alimentarius food safety standards:
```python
safe_until = prepared_at + SHELF_LIFE_HOURS[(category, storage_condition)]
```

### Time Feasibility Check
```python
required_time = travel_eta_minutes + 15  # handover buffer
available_time = remaining_shelf_life_minutes - 30  # safety margin
feasible = (required_time < available_time)
```

### Route Optimisation (2-Opt TSP)
```
1. Nearest Neighbour: greedy construction respecting hard deadlines
2. 2-Opt: iteratively try all (i,j) edge swaps; keep improvements
3. Converges when no improving swap found
```

### Surplus Forecasting
```
cell_avg[weekday][hour] = historical avg kg surplus
seasonal_multiplier = weekend/event-day modifier
predicted_kg = cell_avg × seasonal_multiplier
confidence = based on data density
```

---

## 9. Authentication & Roles

### Firebase Auth
- Email/password sign-in
- JWT Bearer token passed in `Authorization` header to all protected endpoints
- Token validated server-side via `shared/auth.py`

### Demo Credentials (local)
| Role | Email | Password | UID |
|---|---|---|---|
| Admin | admin@gmail.com | foodbridge | (admin account) |
| Donor | donor@gmail.com | foodbridge | donor_taj_palace |
| NGO | ngo@gmail.com | foodbridge | ngo_robin_hood |
| Volunteer | volunteer@gmail.com | foodbridge | vol_arun_kumar |

### Role-Based Access
| Feature | Donor | NGO | Volunteer | Admin |
|---|---|---|---|---|
| Post Surplus | ✅ | ❌ | ❌ | ✅ |
| View own listings | ✅ | ❌ | ❌ | ✅ (all) |
| Accept/Decline offers | ❌ | ✅ | ❌ | ❌ |
| View volunteer routes | ❌ | ❌ | ✅ | ✅ |
| Log handovers | ❌ | ❌ | ✅ | ✅ |
| Admin console | ❌ | ❌ | ❌ | ✅ |
| Impact/Map | ✅ | ✅ | ✅ | ✅ |

---

## 10. Internationalisation (i18n)

### Implementation
- `src/i18n/en.json` — English (base)
- `src/i18n/hi.json` — Hindi (हिंदी)
- `src/i18n/kn.json` — Kannada (ಕನ್ನಡ)
- `src/i18n/context.tsx` — `LanguageProvider` + `useLanguage()` hook
- `src/i18n/index.ts` — `getTranslation(lang)` helper

### Coverage
All UI strings translated: navigation labels, page titles, button text, empty states, loading messages, modal content, error messages, weekday names.

### Usage Pattern
```tsx
const { t } = useLanguage();
// t.donor.title, t.ngo.offer_accepted, t.volunteer.verify_handover, etc.
```

---

## 11. Event-Driven Architecture

### Events
| Event | Publisher | Subscriber | Action |
|---|---|---|---|
| `listing.created` | Listing Service | Matching Service | Trigger NGO matching |
| `match.offered` | Matching Service | Notification Service | Push alert to NGO |
| `offer.accepted` | Matching Service | Logistics Service | Assign volunteer route |
| `route.assigned` | Logistics Service | Notification Service | Push alert to volunteer |
| `pickup.completed` | Logistics Service | Analytics Service | Record impact metrics |

### Event Bus Abstraction
```python
bus = get_event_bus()  # InProcessEventBus (dev) or PubSubEventBus (prod)
bus.publish(topic, data)
bus.subscribe(topic, handler)
```

---

## 12. Deployment

### Docker Compose (local simulation)
```bash
docker-compose up
```
All 6 services + frontend Nginx container run with shared environment variables.

### Google Cloud Run (production)
Each service has its own `Dockerfile`:
- Multi-stage build (Python slim base)
- Non-root user
- Health check endpoint

### Environment Variables
```
ENVIRONMENT=production
GCP_PROJECT_ID=your-project
GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json
GEMINI_API_KEY=your-gemini-key
FIREBASE_WEB_API_KEY=your-firebase-key
EVENT_BUS_TYPE=pubsub
```

### Frontend
- Built with `npm run build` → static `dist/`
- Served by Nginx with SPA routing and gzip compression
- VITE env vars for API base URLs:
  ```
  VITE_API_URL=https://listing.yourapp.run
  VITE_MATCHING_URL=https://matching.yourapp.run
  ...
  ```

---

## 13. Local Development Setup

### Prerequisites
- Python 3.12+ with pip
- Node.js 18+ with npm
- (Optional) Google Gemini API key for real AI analysis

### Backend
```bash
cd foodbridge
# Install shared library
pip install -e services/shared

# Install each service
pip install -r services/listing-service/requirements.txt
pip install -r services/matching-service/requirements.txt
# ... etc

# Start all services
cd scripts
python dev_servers.py
```
Services available at: http://localhost:8001–8006

### Frontend
```bash
cd foodbridge/web
npm install
npm run dev
```
App available at: http://localhost:5173

### API Docs
Each FastAPI service auto-generates OpenAPI docs:
- Listing: http://localhost:8001/docs
- Matching: http://localhost:8002/docs
- Notifications: http://localhost:8003/docs
- Logistics: http://localhost:8004/docs
- Analytics: http://localhost:8005/docs

### Persistent Database
State is stored in `foodbridge/.foodbridge_db.json`. All 6 services share this file via file-locking. Delete it to reset all state.

---

*FoodBridge — Aligning with UN SDG 2 (Zero Hunger) and SDG 12 (Responsible Consumption)*

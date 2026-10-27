# FoodBridge — Complete Demo Guide for Professor Presentation

> **Step-by-step walkthrough of every feature**  
> Follow in order for a complete end-to-end demonstration

---

## Prerequisites — Before You Start

1. **Start backend services** (in terminal 1):
   ```bash
   cd foodbridge/scripts
   python dev_servers.py
   ```
   Wait until you see all 6 services: listing (8001), matching (8002), notification (8003), logistics (8004), analytics (8005), expiry-job (8006)

2. **Start frontend** (in terminal 2):
   ```bash
   cd foodbridge/web
   npm run dev
   ```
   Open: **http://localhost:5173**


---

## SYSTEM ARCHITECTURE: SERVICES & INTERACTION MODEL

FoodBridge is designed as a modular, event-driven microservices architecture built on FastAPI, Pydantic, and an asynchronous Pub/Sub Event Bus. Below is the functional responsibility of each service and how they interact:

### 🧩 What Each Service Does

| Service | Port | Primary Responsibility | Key Technologies | Consumed / Published Events |
|---|:---:|---|---|---|
| **listing-service** | `8001` | Surplus food catalog, FSSAI shelf-life calculator, partner verification queue, escalation monitor, Gemini AI Vision inspection. | FastAPI, Gemini 2.5 Flash / Vision API, Pydantic | **Publishes**: `listing.created`<br>**Subscribes**: `pickup.completed` |
| **matching-service** | `8002` | Geospatial discovery, 6-factor composite scoring engine, NGO offer ranking, cascade escalation timer daemon. | Haversine distance, Scipy/NumPy, Priority Queue | **Subscribes**: `listing.created`<br>**Publishes**: `offer.created`, `offer.accepted`, `offer.declined` |
| **notification-service** | `8003` | Push, SMS, and in-app alerts to donors, NGOs, and volunteers upon status transitions. | Jinja2 templates, async event listeners | **Subscribes**: `offer.created`, `offer.accepted`, `route.assigned` |
| **logistics-service** | `8004` | Volunteer delivery dispatch, 2-Opt Traveling Salesperson (TSP) route optimization, digital handover verification & temperature checkpoint compliance. | 2-Opt TSP Algorithm, Leaflet waypoint generator, FSSAI temperature auditor | **Subscribes**: `offer.accepted`<br>**Publishes**: `route.assigned`, `pickup.completed` |
| **analytics-service** | `8005` | Real-time impact rollups (meals saved, kg diverted, CO2e offset = 2.5×kg), downloadable CSR ESG PDF certificates, ML surplus forecasting. | ReportLab PDF Engine, Linear/Seasonal regression forecasting | **Subscribes**: `pickup.completed` |
| **expiry-job** | `8006` | Background scheduled audit worker running every 60s to automatically expire unaccepted listings past `safe_until`. | Asyncio background task, FSSAI safety policy engine | **Publishes**: `listing.expired` |

---

### 🔄 End-to-End Event Bus Choreography

The services communicate both synchronously (via REST APIs for UI queries) and asynchronously (via Pub/Sub Event Bus for workflow orchestration). Below is the exact sequence of interactions:

```text
[ DONOR ]
    │  (POST /listings)
    ▼
[ listing-service (8001) ]
    │  • Validates FSSAI safety window (safe_until)
    │  • Analyzes food photo with Gemini AI Vision
    │  • Persists listing (Status: available)
    │
    └──► PUBLISH: "listing.created"
              │
              ▼
    [ matching-service (8002) ]
        │  • Finds verified NGOs within 15 km
        │  • Computes 6-Factor Composite Score:
        │    Score = 0.25*Time + 0.20*Distance + 0.15*Capacity
        │          + 0.15*Dietary + 0.15*Reliability + 0.10*Urgency
        │  • Ranks matching NGOs (#1, #2, #3...)
        │  • Generates Offer for Rank #1 NGO
        │
        └──► PUBLISH: "offer.created"
                  │
                  ▼
        [ notification-service (8003) ] ──► Alerts NGO via SMS/Push
                  │
                  ▼
        [ NGO RECIPIENT ]
            │  (POST /offers/{id}/accept  OR  POST /offers/{id}/decline)
            ▼
        [ matching-service (8002) ]
            ├─► IF DECLINED / TIMEOUT:
            │       Cascades offer to Rank #2 NGO; if none in 15km, triggers Admin Escalation
            │
            └─► IF ACCEPTED:
                    PUBLISH: "offer.accepted"
                        │
                        ▼
            [ logistics-service (8004) ]
                │  • Locates nearest active volunteer driver
                │  • Calculates 2-Opt TSP optimal route (Pickup -> Delivery)
                │  • Sets deadline = listing.safe_until - 30 mins
                │  • Generates Waypoint Stops
                │
                └──► PUBLISH: "route.assigned"
                          │
                          ▼
            [ VOLUNTEER DRIVER ]
                │  (POST /routes/{id}/stops/{stop_id}/complete)
                │  • Reaches Taj Palace: Collects hot-held containers
                │  • Reaches Robin Hood Army: Verifies temperature (>63°C)
                │  (POST /handovers)
                │  • Submits digital signoff with temperature reading
                │
                └──► PUBLISH: "pickup.completed"
                          │
                          ▼
            [ analytics-service (8005) ]
                • meals_saved += kg * 2.8
                • kg_diverted += kg
                • co2e_avoided_kg += kg * 2.5 (UN IPCC factor)
                • Generates cryptographic CSR PDF certificate
```

---

## PART 1 — Admin Console (Show Platform Control)

**Login as Admin:**
- Email: `admin@gmail.com`
- Password: `foodbridge`
- You are auto-redirected to the Admin Console

---

### ✅ Feature 1.1 — Microservice Health Telemetry

**What to show:** Click **Admin** in the navigation bar (top).

1. At the top of the Admin Console, see **"Microservices Telemetry & Health Probes"** panel
2. All 6 services show **green dots** with live latency in milliseconds:
   - listing-service · Port 8001 · ~12ms
   - matching-service · Port 8002 · ~15ms
   - notification-service · Port 8003 · ~9ms
   - logistics-service · Port 8004 · ~11ms
   - analytics-service · Port 8005 · ~15ms
   - expiry-job · Port 8006 · ~9ms
3. Click **"Probe Health"** button → watch latency values refresh in real time
4. The panel **auto-refreshes every 10 seconds** automatically

**Points to explain:** Distributed health monitoring, service mesh observability, production-grade telemetry.

---

### ✅ Feature 1.2 — Partner Verification Queue

**What to show:** Below the telemetry panel, see **"Partner Verification Queue"**.

1. Three pending partner applications are shown:
   - **ITC Gardenia Banquets** (Donor, FSSAI: 11223344556677)
   - **Hasiru Dala Feeding Centre** (NGO, License: NGO-8829-KA)
   - **Marriott Convention Center** (Donor, FSSAI: 11899223344551)
2. All show **"pending"** status badge
3. Click **Approve** on "ITC Gardenia Banquets" → badge turns **green "verified"**
4. Click **Reject** on "Hasiru Dala Feeding Centre" → badge turns **red "rejected"**
5. Notice the notice bar: "Approved partner ... Persisted to database."
6. **Refresh the page** → changes persist (saved to Firestore backend, not just local state)

**Points to explain:** Role-based access control, persistent backend state, FSSAI license-based compliance.

---

### ✅ Feature 1.3 — Matching Escalation Monitor

**What to show:** Right column of Admin Console, **"Matching Escalation Alerts"**.

1. Two escalation alerts shown:
   - **Royal Orchid Hotel** — "No responses within 15km. Search radius broadened to 30km." (Active)
   - **Taj Caterers** — "Rank 1 NGO response timeout. Escalated to Koramangala Kitchen." (Already Resolved)
2. Click **"Mark Resolved"** on the Royal Orchid escalation
3. Badge changes from amber **"Active Escalation"** to grey **"Resolved"**
4. Notice bar confirms persistence

**Points to explain:** Cascade matching algorithm, automated escalation when no NGO responds, admin oversight dashboard.

---

## PART 2 — Donor Flow (Post a Surplus Listing)

**Switch role to Donor:**  
In the top navbar, click the role selector dropdown → select **"Donor (donor@gmail.com)"**

You are now viewing as: **Taj Palace Luxury Catering**

---

### ✅ Feature 2.1 — Donor Dashboard Overview

1. See the **Surplus Postings** page with existing active listings
2. Metrics summary bar shows: X active postings, Y portions available, Z kg total weight
3. Existing listings show:
   - **Freshness Clock** — animated countdown to `safe_until` expiry
   - **Gemini AI badge** — "Cooked Catering Meals · 95% confidence"
   - **Status badge** — available/offered/picked_up
4. Click **"Refresh"** → live data reload from backend

---

### ✅ Feature 2.2 — Post New Surplus (Full Form)

Click **"Post Surplus"** (green button, top right).

**Step 1 — Food Details:**
1. Title: "Dinner Banquet: Dal Makhani & Naan"
2. Category: Select **"Cooked Meals"**
3. Storage Condition: **"Hot Hold (>63°C)"**
4. Dietary Type: **"Vegetarian"**
5. Quantity (kg): `35`
6. Portions: `100`
7. Description: "Corporate dinner surplus from evening event"
8. Prepared At: pick today's date and current time

**Step 2 — Location:**
1. Click **"Detect My Location"** → browser GPS → auto-fills coordinates + reverse-geocoded place name (e.g. "MG Road, Bengaluru")
2. You can also type coordinates manually

**Step 3 — Photo Analysis:**
1. Click **"Upload Photo"** or skip (photo optional)
2. If uploading: Gemini AI analyses the image in real time
3. See result: **food_type**, **estimated_portions**, **shelf_life_hours_hint**, **safety_flags**, **confidence score**
4. AI-suggested portions auto-fill the form field

**Step 4 — Review & Submit:**
1. Review all details including auto-calculated **Safe Until** time
2. Click **"Post Surplus"** → listing created in backend
3. Redirected back to Donor Dashboard
4. New listing appears immediately with freshness countdown running
5. Backend automatically triggers the **Matching Engine** (`listing.created` event)

**Points to explain:** Gemini Vision API integration, FSSAI spoilage calculation, geospatial encoding, event-driven architecture.

---

## PART 3 — NGO Feed (Receive & Accept Offers)

**Switch role to NGO:**  
Navbar role selector → **"NGO (ngo@gmail.com)"**

You are now: **Robin Hood Army Bangalore**

---

### ✅ Feature 3.1 — Ranked Offer Feed

Click **"NGO Feed"** in the navigation.

1. See **"Recipient Offer Feed"** — ranked list of surplus offers matched to this NGO
2. Top offer: **"Wedding Feast: Vegetable Dum Biryani"** from Taj Palace Luxury Catering
3. Each offer card shows:
   - **Composite Match Score**: e.g. 91/100
   - **Score Breakdown**:
     - Time Feasibility: 95%
     - Proximity: 88%
     - Capacity Fit: 92%
     - Dietary Match: 100%
     - Reliability: 96%
     - Need Urgency: 85%
   - **AI Analysis badge**: "Gemini · 95% confidence"
   - **Freshness countdown**: time left before safe_until
   - Food details: 42 kg, 120 portions, Hot Hold condition

---

### ✅ Feature 3.2 — Accept an Offer

1. Click **"Accept Offer"** on the top-ranked listing
2. Green success banner: "Offer accepted. Logistics dispatch initiated (Saved permanently)"
3. Offer status changes to **"accepted"** in the Resolved Offers section
4. Backend: `offer.accepted` event published → Logistics service auto-assigns volunteer route
5. Click **"Refresh"** → persistent state confirmed from backend

**Points to explain:** Cascade matching (rank-ordered offers), one-click NGO decision workflow, event-driven logistics trigger.

---

### ✅ Feature 3.3 — Decline an Offer

1. If another offer exists, click **"Decline"**
2. Optionally enter reason
3. Offer moves to Resolved section with **red "declined"** badge
4. Backend automatically cascades offer to next ranked NGO

---

## PART 4 — Volunteer Route (Pickup & Delivery)

**Switch role to Volunteer:**  
Navbar role selector → **"Volunteer (volunteer@gmail.com)"**

You are now: **Arun Kumar** (volunteer driver)

---

### ✅ Feature 4.1 — Optimised Route Itinerary

Click **"Volunteer"** in navigation.

1. See **"Volunteer Delivery Route"** with:
   - Route stats: **6.8 km** total, **~45 mins** estimated
   - Algorithm label: "2-Opt TSP Optimized Itinerary"
2. **Left panel: Leaflet Map** showing:
   - Green marker: **Pickup point** (Taj Palace, MG Road)
   - Blue marker: **Delivery point** (Robin Hood Army, Indiranagar)
   - **Blue polyline** connecting the route
3. **Right panel: Stop Itinerary**:
   - Stop 1: 🟢 PICKUP — Taj Palace Luxury Catering — ETA + Deadline
   - Stop 2: 🔵 DELIVERY — Robin Hood Army Indiranagar — ETA + Deadline
   - Step indicator pins connected by vertical spine line

**Points to explain:** 2-Opt TSP algorithm reduces total distance, hard deadline constraints, Leaflet.js map integration.

---

### ✅ Feature 4.2 — Verify Handover (Pickup)

Click **"Verify Handover"** on Stop 1 (Pickup at Taj Palace).

A modal sheet appears:
1. **Title**: "Verify Food Handover"
2. **Holding Temperature (°C)**: pre-filled `65.0` (hot hold standard)
   - Hint: "FSSAI standard: Hot hold >63°C, Chilled <5°C"
3. **Handover Notes**: pre-filled "Clean sealed containers verified."
4. Click **"Submit Handover"**
5. Stop 1 changes to green **"Handover Verified"** badge with checkmark
6. Success banner confirms: "Handover verified for stop: Taj Palace... Checkpoint permanently saved."
7. **Refresh the page** → stop remains verified (persisted in backend)

**Points to explain:** Digital handover verification, temperature monitoring, FSSAI compliance, persistence across sessions.

---

### ✅ Feature 4.3 — Complete Delivery (Drop-off)

Click **"Verify Handover"** on Stop 2 (Delivery to Robin Hood Army).

1. Enter delivery temperature (e.g. `63.5`)
2. Notes: "All containers sealed, food warm and safe"
3. Click **"Submit Handover"**
4. Both stops now show **"Handover Verified"**
5. Backend: `pickup.completed` event published → Analytics service records impact
6. Route status changes to **"completed"**

---

## PART 5 — Live Map (Real-Time Overview)

Click **"Live Map"** in navigation (public — no login required).

---

### ✅ Feature 5.1 — Interactive Map

1. Leaflet map centred on Bengaluru
2. **Colour-coded markers**:
   - Green pins: Active surplus listings (donors)
   - Blue pins: NGO shelters
   - Orange/red pins: In-transit / picked-up
3. **Click any marker** → popup with:
   - Name, food type, portions, distance, status
4. **Zoom in/out** to explore different areas
5. Route polylines show volunteer paths

---

## PART 6 — Impact Dashboard (Analytics & CSR)

Click **"Impact"** in navigation (public — no login required).

---

### ✅ Feature 6.1 — Animated Impact Counters

1. Watch the **four animated roll-up counters**:
   - 🍽️ **Meals Saved**: 410+ meals
   - ⚖️ **Food Diverted**: 142.5+ kg
   - 🌿 **CO2e Avoided**: 356.25+ kg
   - 🏆 **Rescues Completed**: 8+
2. Numbers animate smoothly on page load
3. Aligned with **UN SDG 2** (Zero Hunger) and **SDG 12** (Responsible Consumption)

---

### ✅ Feature 6.2 — CSR Certificate Download

In the **Monthly CSR Impact Certificate** card (left):
1. See beneficiary: **Taj Palace Luxury Catering**
2. Certified Period: **October 2026**
3. GHG Offset Standard: **UN SDG 12.3**
4. Click **"Generate PDF Certificate"** → browser downloads a real PDF
5. Open the PDF to show: donor name, impact metrics table, UN SDG badge, cryptographic hash

**Points to explain:** ReportLab PDF generation, corporate ESG compliance reporting, auto-generated verifiable certificates.

---

### ✅ Feature 6.3 — Surplus Forecasting Engine

In the **Surplus Forecasting** card (right):
1. **Day of Week**: Select "Friday"
2. **Time Window**: Select "22:00 (Banquet Peak)"
3. Results appear instantly:
   - **Predicted Surplus**: X kg
   - **Expected Portions**: Y meals
   - **Confidence Score**: Z%
   - Model details + seasonal multiplier
4. Try different day/time combinations → watch predictions change

**Points to explain:** ML-based forecasting, seasonal trend analysis, commercial meal service cycle patterns.

---

## PART 7 — Language Switching (i18n)

Works from **any page** — demonstrate on the NGO Feed or Donor Dashboard.

---

### ✅ Feature 7.1 — Real-Time Language Switching

1. Find the **language selector** in the top navbar (Globe icon + dropdown)
2. Switch from **EN** → **HI** (Hindi)
   - Navigation: दाता · एनजीओ फीड · स्वयंसेवक · लाइव मैप · प्रभाव · प्रशासक
   - Page titles, buttons, labels, empty states all in Hindi
3. Switch to **KN** (Kannada)
   - Navigation: ದಾನಿ · ಎನ್‌ಜಿಒ ಫೀಡ್ · ಸ್ವಯಂಸೇವಕ · ಲೈವ್ ನಕ್ಷೆ · ಪ್ರಭಾವ · ನಿರ್ವಾಹಕ
4. Switch back to **EN** → instant re-render

**Points to explain:** React Context for global i18n, zero prop-drilling, instant re-render across all components, India-relevant language support.

---

## PART 8 — Location Detection

Visible in the **top navbar**, left of the language selector.

---

### ✅ Feature 8.1 — Reverse Geocoded Location Pill

1. A location pill shows: **"Palace Grounds, Bengaluru"** with coordinates
2. Click the location pill → GPS detection triggered
3. Shows spinning loader: **"Detecting place..."**
4. After detection: real place name appears (reverse geocoded via Nominatim)
5. Pill turns green with checkmark for 4 seconds to confirm success

**Points to explain:** Browser Geolocation API, reverse geocoding (Nominatim/OpenStreetMap), UX feedback pattern.

---

## PART 9 — Post Surplus Form (Advanced Features)

Switch back to **Donor** role and click **Post Surplus** again to show deeper features.

---

### ✅ Feature 9.1 — Gemini AI Photo Analysis (Live)

1. In the photo upload section, select any food image
2. Watch the **loading spinner** as Gemini analyses the image
3. Results panel appears with:
   - Food type identified
   - Portions estimate
   - Shelf life hint (hours)
   - Safety flags (temperature, container, visual quality)
   - Confidence percentage
   - Source: "gemini" or "heuristic_fallback"
4. Click **"Use AI Suggestion"** → form fields auto-populate

---

### ✅ Feature 9.2 — Spoilage-Aware Safe Until

1. After setting Prepared At + Category + Storage Condition
2. See **"Safe Until"** field auto-calculated and displayed
3. Change storage from "Hot Hold" → "Ambient" → watch safe window shrink
4. This enforces food safety: no listing can have unrealistically long windows

---

## PART 10 — API Documentation (Developer Feature)

Show the **auto-generated FastAPI docs** in a browser tab.

1. Open: http://localhost:8001/docs
2. Show Listing Service Swagger UI:
   - All endpoints documented
   - Request/response schemas auto-generated from Pydantic models
   - "Try it out" buttons work live
3. Open: http://localhost:8005/docs
4. Show Analytics Service endpoints including `/analytics/certificate/{donor_id}`

**Points to explain:** FastAPI auto-docs, Pydantic-driven schema generation, production-ready API documentation.

---

## PART 11 — Automated Multi-Role Simulation (Admin, Donor, NGO, Volunteer)

During demonstrations or professor evaluations, manually logging in and switching between 4 distinct accounts (Admin, Donor, NGO, Volunteer) can take 10+ minutes. FoodBridge includes an **automated multi-actor simulation suite** that demonstrates all interactions, microservice event handoffs, and business logic across all 4 roles in real time!

---

### 🚀 How to Run the Simulator

Open a terminal window in the `foodbridge` directory:

```bash
# Recommended Presentation Speed (Paced for live speaking):
python -u simulator/demo_sim.py --speed 3

# Fast Mode (Complete demo in 20-30 seconds):
python -u simulator/demo_sim.py --speed 8

# Real-Time Mode (1x speed, realistic timing):
python -u simulator/demo_sim.py --speed 1
```

> **💡 Professor Presentation Tip (Dual-Screen Setup):**
> Arrange your screen with **Terminal on the Left** and **Browser (`http://localhost:5173`) on the Right**.
> When the terminal runs the simulation, watch the Web UI dynamically reflect newly posted listings, accepted offers, updated volunteer routes, and real-time impact counters!

---

### 🎬 Detailed Simulation Phase Breakdown

The simulation script (`simulator/demo_sim.py`) executes 7 sequential phases simulating real users across all 4 roles:

```text
====================================================================
  FOODBRIDGE - COMPLETE DEMONSTRATION SIMULATOR
  Covers all roles: Admin | Donor | NGO | Volunteer
====================================================================
```

#### 📡 Phase 0: Service Health Check & Telemetry
- **Who:** System Daemon
- **What happens:** Directly probes HTTP health endpoints across all microservices (`listing:8001`, `matching:8002`, `notification:8003`, `logistics:8004`, `analytics:8005`).
- **Terminal Output:** Displays `[OK] UP` status for every active service.
- **Why it matters:** Demonstrates service mesh resilience and verifies all dependencies are reachable before workflow dispatch.

#### 🛡️ Phase 1: Admin Role — Partner Verification & Escalation Audit
- **Who:** System Admin (`admin@gmail.com`)
- **What happens:** 
  1. Inspects the pending partner verification queue for new commercial donors and NGOs.
  2. Evaluates submitted FSSAI food business licenses.
  3. Approves verified partners (`ITC Gardenia Banquets`, `Marriott Convention Center`).
  4. Scans the **Matching Escalation Monitor** for listings with no nearby NGOs, automatically expanding matching radius from 15km to 30km.
- **Terminal Output:**
  ```text
  [ADMIN    ] Found 2 pending verification requests -> queue depth: 2
  [ADMIN    ] Reviewing: ITC Gardenia Banquets (DONOR) -> FSSAI: 11223344556677
  [ADMIN    ] [OK] APPROVED: ITC Gardenia Banquets -> now active in FoodBridge network
  [ADMIN    ] Checking escalation alerts...
  [ADMIN    ] Found 1 unresolved escalation(s) -> auto-broadening search radius to 30km
  ```

#### 🍲 Phase 2: Donor Role — Posting Diverse Surplus Listings
- **Who:** Commercial Donor (`donor@gmail.com` / Taj Palace Luxury Catering)
- **What happens:**
  Posts 3 realistic food surplus donations with varying FSSAI storage constraints:
  1. **Hot Hold Meals:** 35 kg / 100 portions Dal Makhani & Jeera Rice (72°C hot hold, 3-hour safe window).
  2. **Chilled Breakfast:** 22 kg / 70 portions Hotel Breakfast Buffet (2–4°C chilled, 6-hour safe window).
  3. **Ambient Produce:** 15 kg / 45 portions Fresh Fruit Basket (Ambient storage, 48-hour safe window).
- **Under the Hood:**
  - Auto-calculates `safe_until` timestamp using FSSAI category tables.
  - Passes photos to Gemini AI Vision for portion estimation and safety flagging.
  - Publishes `listing.created` event -> triggers `matching-service`.
- **Terminal Output:**
  ```text
  [DONOR    ] Posting: Corporate Lunch Surplus: Dal Makhani, Jeera Rice & Naan...
  [DONOR    ]   [OK] LISTED (ID: list_402fbd090ada) -> safe_until: 15:44:29 UTC
  [SYSTEM   ]   -> listing.created event published to matching-service
  [SYSTEM   ]   -> Matching engine scoring all NGOs in radius...
  ```

#### 🤝 Phase 3: NGO Role — 6-Factor Ranked Match & 1-Click Acceptance
- **Who:** NGO Recipient (`ngo@gmail.com` / Robin Hood Army Bangalore)
- **What happens:**
  1. Robin Hood Army checks their prioritized surplus feed.
  2. Matching Engine calculates multi-criteria utility score and outputs full breakdown:
     - **Time Feasibility:** 100% (Volunteer can deliver well before `safe_until - 30m`)
     - **Proximity:** 74% (Distance < 6 km)
     - **Capacity Fit:** 63% (Fits NGO daily distribution capacity)
     - **Dietary Match:** 100% (Matches requested vegetarian profile)
     - **Reliability Score:** 96% (Verified donor compliance score)
     - **Need Urgency:** 70% (Shelter priority index)
  3. NGO clicks **Accept Donation**.
  4. Backend publishes `offer.accepted` -> alerts donor and prompts logistics service to dispatch route.
- **Terminal Output:**
  ```text
  [NGO      ] TOP OFFER: Hotel Breakfast Buffet -> Score: 85/100 - Rank #1
  [NGO      ] Score Breakdown:
                Time Feasibility : 100%
                Proximity        : 74%
                Capacity Fit     : 63%
                Dietary Match    : 100%
                Reliability Score: 96%
                Need Urgency     : 70%
  [NGO      ] Clicking ACCEPT DONATION...
  [NGO      ] [OK] OFFER ACCEPTED! -> listing claimed, logistics triggered
  [SYSTEM   ] -> offer.accepted event -> notification-service -> donor + volunteer notified
  [SYSTEM   ] -> logistics-service computing 2-Opt TSP pickup route...
  ```

#### ⏱️ Phase 4: NGO Role — Decline & Cascade Escalation
- **Who:** Secondary NGO (`ngo_koramangala` / Koramangala Community Kitchen)
- **What happens:**
  1. Demonstrates what occurs when an NGO has no storage or has already met daily capacity.
  2. NGO submits a Decline with reason: *"At full capacity today"*.
  3. System triggers **Cascade Engine**: The listing is instantly offered to the next highest-scoring candidate (Rank #2).
  4. If no candidate responds within the timeout window (600s), an Admin Escalation is logged.

#### 🚚 Phase 5: Volunteer Role — 2-Opt TSP Dispatch & Digital Handover
- **Who:** Volunteer Driver (`volunteer@gmail.com` / Arun Kumar)
- **What happens:**
  1. Volunteer receives assigned route (`rt_opt_blr_01`, 6.8 km total distance).
  2. Navigates to **Stop 1 (PICKUP)** at Taj Palace: Marks pickup complete.
  3. Navigates to **Stop 2 (DELIVERY)** at Robin Hood Army: Marks delivery complete.
  4. **FSSAI Handover Compliance Check:** Logs holding temperature (66.5°C verified, meeting >63°C regulatory requirement), container integrity notes, and verifies digital signatures.
  5. Publishes `pickup.completed` event.
- **Terminal Output:**
  ```text
  [VOLUNTEER] Route: rt_opt_blr_01 -> 2 stops - 6.8km
  [VOLUNTEER]   PICKUP: Taj Palace Luxury Catering -> ETA: 11:02:30
  [VOLUNTEER]   [OK] PICKUP COMPLETE
  [VOLUNTEER]   DELIVERY: Robin Hood Army Indiranagar -> ETA: 11:32:30
  [VOLUNTEER]   [OK] DELIVERY COMPLETE
  [VOLUNTEER] Logging final food handover at delivery point...
  [VOLUNTEER]   [OK] HANDOVER LOGGED -> Temp: 66.5 C - Signatures: OK
  [SYSTEM   ]   -> pickup.completed event -> analytics-service records impact
  [SYSTEM   ]   -> Donor receives CO2e impact certificate
  ```

#### 📊 Phase 6: Analytics Service — Real-Time Impact & ML Forecast
- **Who:** System Analytics & Corporate ESG Engine
- **What happens:**
  1. Fetches aggregated live metrics computed from verified handovers:
     - **Total Meals Saved:** `4,625 meals` (calculated as `kg × 2.8`)
     - **Food Diverted from Landfills:** `1,670 kg`
     - **CO2e Greenhouse Gas Avoided:** `4,175 kg CO2e` (IPCC conversion factor: `2.5 kg CO2e per kg food`)
     - **Completed Rescues:** `31 successful rescues`
  2. Queries ML Surplus Forecasting model for Friday 22:00 (banquet peak) predicting expected surplus in kg.
- **Terminal Output:**
  ```text
  ============================================
        FOODBRIDGE LIVE IMPACT TELEMETRY      
  ============================================
  Total Meals Saved    :    4625 meals
  Food Diverted        :  1670.0 kg
  CO2e Avoided         :  4175.0 kg CO2e
  Completed Rescues    :      31
  ============================================
  Forecast (Fri 22:00): 48.5 kg expected surplus
  ```

#### 🔍 Phase 7: Admin Role — Post-Demo Audit & Latency Telemetry
- **Who:** Admin (`admin@gmail.com`)
- **What happens:**
  Probes all 6 services for live latency benchmarks and confirms system stability with active inventory count.
- **Terminal Output:**
  ```text
  [OK] listing-service                port 8001   0.0ms
  [OK] matching-service               port 8002   0.0ms
  [OK] notification-service           port 8003  14.0ms
  [OK] logistics-service              port 8004  17.0ms
  [OK] analytics-service              port 8005  17.2ms
  [OK] expiry-job                     port 8006  18.2ms
  [ADMIN    ]   7 available listings in system
  ```

---

### 🧪 Alternative Scenario-Based Simulation Runner

For automated regression testing or scripted scenarios, FoodBridge also includes `run_scenario.py`:

```bash
python simulator/run_scenario.py --scenario simulator/scenarios/full_demo.json
```
This loads a declarative JSON scenario containing predefined listings, offers, and route waypoints, validating API response schemas at each step.

---

## Summary: Features Demonstrated

| # | Feature | Where |
|---|---|---|
| **0.1** | **Microservice Architecture & Pub/Sub Event Bus** | **System Core (All 6 Services)** |
| 1.1 | Microservice health telemetry | Admin Console |
| 1.2 | Partner verification (Approve/Reject) | Admin Console |
| 1.3 | Escalation monitoring | Admin Console |
| 2.1 | Donor dashboard with freshness clocks | Donor page |
| 2.2 | Full surplus posting form | Post Surplus |
| 2.3 | Gemini AI photo analysis | Post Surplus |
| 2.4 | GPS + reverse geocoding | Post Surplus |
| 2.5 | Spoilage-aware safe_until | Post Surplus |
| 3.1 | Ranked composite score feed (6-factor) | NGO Feed |
| 3.2 | Accept offer (one-click) | NGO Feed |
| 3.3 | Decline + cascade | NGO Feed |
| 4.1 | 2-Opt TSP route on map | Volunteer |
| 4.2 | Handover verification modal | Volunteer |
| 4.3 | Persistent checkpoint (refresh) | Volunteer |
| 5.1 | Live map with all markers | Live Map |
| 6.1 | Animated impact counters | Impact |
| 6.2 | CSR PDF certificate download | Impact |
| 6.3 | Surplus forecasting by day/time | Impact |
| 7.1 | Language switching EN/HI/KN | Navbar |
| 8.1 | Location pill + GPS detect | Navbar |
| 10 | FastAPI auto-docs | Browser :8001/docs |
| **11.1** | **Full 4-Role End-to-End Simulator (`demo_sim.py`)** | **Terminal (`python simulator/demo_sim.py`)** |
| **11.2** | **Declarative JSON Scenario Runner (`run_scenario.py`)** | **Terminal (`full_demo.json`)** |
| **11.3** | **Live Dual-Screen Terminal + UI Orchestration** | **Simultaneous Terminal & Web UI** |

---

## Talking Points for Q&A

**"What does each service do and how do they communicate?"**
> FoodBridge has 6 specialized microservices: `listing-service` (catalog & FSSAI safety), `matching-service` (geospatial matching & scoring), `notification-service` (alerts), `logistics-service` (2-Opt TSP routing), `analytics-service` (impact calculation & CSR PDF), and `expiry-job` (automated safety expiry).
> They interact synchronously via REST APIs for immediate web queries, and asynchronously via an in-memory/Pub-Sub Event Bus for decoupled event orchestration (`listing.created` -> `offer.created` -> `offer.accepted` -> `route.assigned` -> `pickup.completed`).

**"How does the automated multi-agent simulation work?"**
> `simulator/demo_sim.py` automates the interactions across all 4 system actors (Admin, Donor, NGO, Volunteer). It connects directly to the live microservice APIs, posting realistic surplus entries, executing matching, demonstrating offer acceptance and decline cascade, simulating 2-Opt TSP delivery with FSSAI temperature verification, and updating impact metrics in real time.

**"How does it scale to production?"**
> The same codebase deploys to Google Cloud Run with zero code changes — environment variables toggle from file-backed storage to Cloud Firestore, and from in-process events to Cloud Pub/Sub. Docker Compose is provided for local, docker-compose.prod.yml for cloud.

**"How is food safety enforced?"**
> Every listing has a `safe_until` timestamp computed from FSSAI standards. The matching algorithm has a hard time-feasibility filter: if the volunteer cannot reach the NGO before `safe_until - 30 minutes`, the listing is not offered to that NGO. Volunteers must also digitally log temperature (e.g. >63°C for hot hold) before handing over food.

**"What happens if an NGO declines or does not respond?"**
> The cascade engine escalates: Rank 1 NGO has a 600-second acceptance window. If declined or timed out, Rank 2 immediately receives the offer. If no NGO responds within 15 km, an escalation alert appears in the Admin Console and the search radius is automatically broadened to 30–40 km.

**"Is the AI mandatory?"**
> No. Gemini Vision analysis is optional — if the API key is unavailable, a heuristic fallback (`source: "heuristic_fallback"`) uses food category rules. The platform works without AI credentials.

**"How does impact get calculated?"**
> When a volunteer logs a delivery handover, the `pickup.completed` event is published. The Analytics Service subscribes, computes `meals_saved = kg × 2.8` and `CO2e_avoided = kg × 2.5` (IPCC factor), and stores an `ImpactRecord`. The CSR PDF is generated from aggregated records.


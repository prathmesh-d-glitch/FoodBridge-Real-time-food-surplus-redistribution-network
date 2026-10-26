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

## Summary: Features Demonstrated

| # | Feature | Where |
|---|---|---|
| 1.1 | Microservice health telemetry | Admin Console |
| 1.2 | Partner verification (Approve/Reject) | Admin Console |
| 1.3 | Escalation monitoring | Admin Console |
| 2.1 | Donor dashboard with freshness clocks | Donor page |
| 2.2 | Full surplus posting form | Post Surplus |
| 2.3 | Gemini AI photo analysis | Post Surplus |
| 2.4 | GPS + reverse geocoding | Post Surplus |
| 2.5 | Spoilage-aware safe_until | Post Surplus |
| 3.1 | Ranked composite score feed | NGO Feed |
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

---

## Talking Points for Q&A

**"How does it scale to production?"**
> The same codebase deploys to Google Cloud Run with zero code changes — environment variables toggle from file-backed storage to Cloud Firestore, and from in-process events to Cloud Pub/Sub. Docker Compose is provided for local, docker-compose.prod.yml for cloud.

**"How is food safety enforced?"**
> Every listing has a `safe_until` timestamp computed from FSSAI standards. The matching algorithm has a hard time-feasibility filter: if the volunteer cannot reach the NGO before `safe_until - 30 minutes`, the listing is not offered to that NGO.

**"What happens if no NGO responds?"**
> The cascade system escalates: Rank 1 NGO has 600 seconds to respond. If they don't, Rank 2 gets the offer. If no one within 15 km responds, an escalation alert appears in the Admin Console and the search radius is broadened.

**"Is the AI mandatory?"**
> No. Gemini Vision analysis is optional — if the API key is unavailable, a heuristic fallback (`source: "heuristic_fallback"`) uses food category rules. The platform works without AI credentials.

**"How does impact get calculated?"**
> When a volunteer logs a delivery handover, the `pickup.completed` event is published. The Analytics Service subscribes, computes `meals_saved = kg × 2.8` and `CO2e_avoided = kg × 2.5` (IPCC factor), and stores an `ImpactRecord`. The CSR PDF is generated from aggregated records.

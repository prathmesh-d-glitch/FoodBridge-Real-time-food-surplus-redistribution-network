# FoodBridge: 5-Minute Technical Demonstration Script

This script provides an exact, minute-by-minute live presentation guide for project examiners, university evaluators, or technical interviewers.

---

## Preparation (Pre-Demo Setup)
Execute the local dev stack in your terminal:
```bash
# Terminal 1: Start backend microservice mesh
python scripts/dev_servers.py

# Terminal 2: Start frontend PWA dev server
cd web && npm run dev
```
Open your browser to `http://localhost:5173`. Ensure your browser is zoomed to 100% and dark mode is active.

---

## Minute 0:00 – 1:00: The Problem, Philosophy & Cloud Architecture

### What to say:
> "Good morning, evaluators. Over 40% of urban cooked food in hotels, banquets, and hostels is discarded while millions face nutritional insecurity. The fundamental bottleneck is not lack of food or lack of shelters—it is the **decay window**. Cooked food spoils within 3 to 6 hours. Traditional manual dispatch takes too long, resulting in spoiled food or food safety hazards.
>
> We built **FoodBridge: A Real-Time Food Surplus Redistribution Network**. 
> As you can see in our architecture diagram, FoodBridge is entirely **cloud-native, serverless, and event-driven**. It is built on Google Cloud Platform using **Python FastAPI microservices on Cloud Run**, an asynchronous event mesh via **Cloud Pub/Sub push subscriptions**, point-in-time delayed escalations using **Cloud Tasks**, spatial indexing in **Firestore**, and predictive ML in **BigQuery**.
> 
> Crucially, for testing and evaluation, we built an abstracted **in-memory event bus and database adapter**, meaning everything runs locally right now with **zero cloud credentials** required."

### What to show:
- Point to the clean terminal windows with the running microservices on ports 8001, 8002, 8004, 8005 and Vite on 5173.
- Show the architecture diagram from `docs/architecture.md`.

---

## Minute 1:00 – 2:00: Donor Flow, Multimodal AI & Spoilage Computation

### What to say:
> "Let's begin from the donor's perspective. Here in the FoodBridge PWA, we log in as the head chef of **The Grand Palace Banquets**. 
> We have an active post-event surplus of 85 portions of hot-held Biryani. 
> Notice when we upload a photo or click analyze, our **Gemini 1.5 Flash AI inspection endpoint** classifies the food category, validates portion sizing, and performs hygiene safety checks.
> 
> Watch how FoodBridge computes `safe_until`. It combines the food category, preparation timestamp, and hot-hold storage condition to establish an exact safe consumption deadline of 4 hours."

### What to show:
- Navigate to `/donor` -> `/post-surplus`.
- Click **"Use Sample Event Data"** or fill portions: 85, category: "Cooked Meals", storage: "Hot-Hold (>60C)".
- Click **"Analyze Photo with AI"** to showcase the Gemini suggestions modal.
- Click **"Post Surplus Food"**. Show the listing appearing instantly with its status as `AVAILABLE`.

---

## Minute 2:00 – 3:00: Spoilage Hard Filter & 6-Factor Composite Explainability

### What to say:
> "The instant the listing is committed, an asynchronous `listing.created` event is published to our Cloud Pub/Sub mesh.
> The **matching-service** consumes this event and performs a two-stage evaluation.
> 
> First, our **Hard Spoilage Filter** mathematically verifies that candidate NGOs can physically travel, load, and consume the food before `safe_until` minus our 30-minute safety buffer. If traffic makes this impossible, the candidate is discarded immediately.
> 
> Second, eligible candidates are scored using our **6-Factor Composite Algorithm**:
> $0.30 \times \text{time\_feasibility} + 0.25 \times \text{proximity} + 0.15 \times \text{capacity\_fit} + 0.10 \times \text{dietary} + 0.15 \times \text{reliability} + 0.05 \times \text{urgency}$.
> 
> Notice that every match returns a 100% explainable factor breakdown."

### What to show:
- Switch to the **NGO Feed** page (`/ngo`).
- Point out the active offer card displaying the **Match Explainer Badge** with the 6 factor bars.
- Point to the **Freshness Clock** dynamically counting down remaining shelf life and offer timeout.

---

## Minute 3:00 – 4:00: Cascading Offers & 2-Opt Volunteer Route Optimization

### What to say:
> "What happens if an NGO is busy and cannot take the food? 
> FoodBridge solves the 'indecisive recipient deadlock' using **Cascading Offers**. 
> The offer is clamped between 3 to 15 minutes based on shelf life. If the NGO declines or if the Cloud Task timeout fires, the system automatically cancels the offer and escalates to Rank 2.
> 
> Let's accept this offer as **Asha Shelter Home**.
> Notice how the state transitions atomically. The matching service publishes `offer.accepted`, which triggers our **logistics-service**.
> 
> In the Volunteer view, our **2-Opt Travelling Salesperson route optimizer** batches pending pickups and drop-offs, ensuring no pickup deadline is violated while minimizing transit mileage.
> The volunteer records the handover temperature—confirming $68^\circ\text{C}$ safe hot-hold—and completes delivery."

### What to show:
- In NGO Feed, click **"Accept Offer"**.
- Navigate to `/volunteer` to show the optimized route with ordered stops and ETAs.
- Click **"Confirm Pickup (Record Temp: 68°C)"** and **"Confirm Handover Complete"**.

---

## Minute 4:00 – 5:00: Live Map, Impact Dashboard, CSR Certificate & Simulation

### What to say:
> "Now let's observe the network-level results.
> On our **Live Map**, built with Leaflet and OpenStreetMap, we see live spatial markers for donors, NGOs, and active volunteer couriers across Bengaluru.
> 
> Switching to the **Impact Dashboard**, the completion of that delivery instantly incremented our global metrics:
> Total meals saved, kilograms diverted from landfills, and CO2-equivalent emissions avoided, calculated at 2.5 kg CO2e per kg of food diverted.
> 
> Donors can download their **tamper-proof CSR Impact Certificate** with an embedded cryptographic SHA-256 verification hash for corporate ESG compliance.
> 
> Finally, to prove that the architecture handles high concurrency, let's run our **Simulator** with the 'wedding_rush' scenario at 10x speed multiplier."

### What to show:
- Navigate to `/live-map` showing real-time clustered nodes and routes.
- Navigate to `/impact` showing animated counters and click **"Download CSR Impact Certificate (PDF)"**.
- In Terminal 3, run: `python simulator/simulate.py --scenario simulator/scenarios/wedding_rush.json --speed 10`.
- Watch the console stream rapid dispatches and refresh `/impact` to show meals saved jumping by hundreds in seconds!
- Conclude: *"Thank you. We are ready for your technical questions."*

# FoodBridge: Cloud-Native System Architecture

## 1. Executive Summary & Philosophy
FoodBridge is an event-driven, serverless platform designed to solve the critical problem of urban food surplus redistribution before cooked or perishable items spoil. Because cooked food degrades rapidly (often having a safe window of 2 to 6 hours), every component in FoodBridge prioritizes **zero-latency dispatch**, **eventual consistency with guaranteed delivery**, **explainable matching**, and **graceful fallback**.

The platform is designed around **Google Cloud Platform (GCP)** managed serverless primitives, ensuring high availability, zero idle costs (free-tier friendly), and automated horizontal scalability up to tens of thousands of concurrent requests.

---

## 2. High-Level Component Topology

```mermaid
flowchart TB
    subgraph Clients["Edge & Clients"]
        DonorApp["Donor PWA (Mobile/Web)"]
        NgoApp["NGO PWA (Mobile/Web)"]
        VolApp["Volunteer PWA (Mobile/Web)"]
        AdminApp["Admin Dashboard"]
    end

    subgraph CDN["Edge Ingress & Static Delivery"]
        FBHosting["Firebase Hosting / Cloud CDN"]
    end

    subgraph Gateways["API Ingress & Identity"]
        GCPAuth["Firebase Auth (Custom Claims: donor, ngo, volunteer, admin)"]
        CloudRunIngress["Cloud Run HTTPS Microservices"]
    end

    subgraph Microservices["Serverless Microservices (Cloud Run)"]
        ListingSvc["listing-service (Port 8001)<br/>• Photo Gemini AI<br/>• Spoilage safe_until computation"]
        MatchingSvc["matching-service (Port 8002)<br/>• 6-Factor Composite Scoring<br/>• Cascading Offer Engine"]
        NotifSvc["notification-service (Port 8003)<br/>• FCM Push Dispatches<br/>• Pluggable SMS Gateway"]
        LogisticsSvc["logistics-service (Port 8004)<br/>• 2-Opt Multi-Stop Routing<br/>• Handover Checkpoints"]
        AnalyticsSvc["analytics-service (Port 8005)<br/>• CO2e Impact Aggregator<br/>• CSR PDF Generation<br/>• Surplus Forecasting"]
        ExpiryJob["expiry-job (Port 8006)<br/>• Cloud Scheduler Cron Scanner<br/>• Timeout & Expired State Machine"]
    end

    subgraph EventMesh["Asynchronous Event Mesh"]
        PubSub["Cloud Pub/Sub Topics<br/>listing.created, match.offered, offer.accepted, etc."]
        CloudTasks["Cloud Tasks Queue<br/>Delayed Cascading Offer Timeouts"]
        DeadLetter["Dead Letter Topics & Alerting"]
    end

    subgraph DataStorage["Managed Cloud Persistence"]
        Firestore["Cloud Firestore (Native Mode)<br/>• Geohash Spatial Indexing<br/>• Real-time onSnapshot Synchronization"]
        GCS["Cloud Storage<br/>• Food Item Photos & CSR Certificates"]
        BigQuery["BigQuery Data Warehouse<br/>• Partitioned Impact & Audit Logs"]
    end

    %% Client Interactions
    DonorApp --> FBHosting
    NgoApp --> FBHosting
    VolApp --> FBHosting
    AdminApp --> FBHosting

    DonorApp --> GCPAuth
    DonorApp --> ListingSvc
    NgoApp --> MatchingSvc
    VolApp --> LogisticsSvc
    AdminApp --> AnalyticsSvc

    %% Service to Storage
    ListingSvc --> Firestore
    ListingSvc --> GCS
    MatchingSvc --> Firestore
    LogisticsSvc --> Firestore
    AnalyticsSvc --> Firestore
    AnalyticsSvc --> BigQuery
    ExpiryJob --> Firestore

    %% Event Connections
    ListingSvc -- "listing.created" --> PubSub
    PubSub -- "Push to /events/*" --> MatchingSvc
    MatchingSvc -- "match.offered" --> PubSub
    PubSub -- "Push to /events/*" --> NotifSvc
    MatchingSvc -- "Schedule Timeout (3-15m)" --> CloudTasks
    CloudTasks -- "Dispatch Timeout Callback" --> MatchingSvc
    MatchingSvc -- "offer.accepted" --> PubSub
    PubSub -- "Push to /events/*" --> LogisticsSvc
    LogisticsSvc -- "pickup.completed" --> PubSub
    PubSub -- "Push to /events/*" --> AnalyticsSvc
```

---

## 3. End-to-End Event Flow & Sequence Diagrams

### 3.1. Food Donation Ingestion, AI Safety Inspection & Cascading Match

The following sequence diagram details the full cycle: from a donor posting food, through Gemini multimodal safety analysis, composite scoring, and the cascading offer lifecycle.

```mermaid
sequenceDiagram
    autonumber
    actor Donor as Restaurant Donor
    participant LS as listing-service
    participant Gemini as Google Gemini AI
    participant FS as Cloud Firestore
    participant PS as Cloud Pub/Sub
    participant MS as matching-service
    participant CT as Cloud Tasks
    participant NS as notification-service
    actor NGO1 as NGO Priority 1
    actor NGO2 as NGO Priority 2

    Donor->>LS: POST /api/listings (category, prepared_at, portions, photo_url)
    LS->>Gemini: Inspect photo (visual quality, portion validation, safety flags)
    alt Gemini API Key Available
        Gemini-->>LS: {food_type, portions, shelf_life_hours, confidence, safety_flags}
    else API Key Missing / Quota Exceeded
        LS-->>LS: Fallback to deterministic rule table (category base hours * storage factor)
    end
    LS->>LS: Calculate safe_until = prepared_at + shelf_life
    LS->>FS: Write listing (status: "AVAILABLE", geohash: "tdr1v4")
    LS->>PS: Publish event: "listing.created"
    LS-->>Donor: 201 Created (listing_id, safe_until, suggestions)

    PS->>MS: Push subscription: POST /events/listing-created
    MS->>FS: Query active NGOs within initial radius (geohash bounding box)
    MS->>MS: Filter: (ETA + handover_buffer) < (safe_until - 30m safety_margin)
    MS->>MS: Calculate 6-factor composite match scores
    MS->>FS: Save ranked match candidates
    MS->>FS: Create Offer for Rank 1 (status: "OFFERED", timeout: 8 min)
    MS->>CT: Schedule Cloud Task timeout execution in 8 min
    MS->>PS: Publish event: "match.offered" (offer_id, ngo_id, rank=1)
    PS->>NS: Push subscription: POST /events/match-offered
    NS->>NGO1: Send FCM Push & SMS Notification ("Fresh Meal Available - Respond in 8m")

    alt NGO 1 Declines or Cloud Task Timeout Fires
        NGO1->>MS: POST /api/offers/{id}/decline (or Cloud Tasks trigger)
        MS->>FS: Update Offer 1 status: "DECLINED" / "EXPIRED"
        MS->>MS: Auto-escalate to Rank 2 candidate (NGO 2)
        MS->>FS: Create Offer for Rank 2 (timeout: 6 min)
        MS->>CT: Schedule next Cloud Task timeout in 6 min
        MS->>PS: Publish event: "match.offered" (offer_id, ngo_id, rank=2)
        PS->>NS: Push notification
        NS->>NGO2: Send FCM Push & SMS
    end

    NGO2->>MS: POST /api/offers/{id}/accept
    MS->>FS: Update Offer 2: "ACCEPTED", Listing: "MATCHED"
    MS->>PS: Publish event: "offer.accepted" (listing_id, ngo_id)
```

---

### 3.2. Volunteer Logistics, Route Batching & Impact Finalization

```mermaid
sequenceDiagram
    autonumber
    participant PS as Cloud Pub/Sub
    participant LogSvc as logistics-service
    participant FS as Cloud Firestore
    actor Vol as Volunteer Courier
    participant AS as analytics-service
    participant BQ as BigQuery

    PS->>LogSvc: Push event: "offer.accepted"
    LogSvc->>FS: Retrieve pickup location (Donor) & dropoff location (NGO)
    LogSvc->>LogSvc: Run 2-Opt TSP Route Optimizer with hard pickup deadlines
    LogSvc->>FS: Update Volunteer active route with ordered stops and ETAs
    Vol->>LogSvc: GET /api/logistics/routes/active
    LogSvc-->>Vol: Ordered Route (Donor Pickup -> NGO Dropoff, ETAs)

    Vol->>LogSvc: POST /api/logistics/handover/pickup (temp: 65°C, photo)
    LogSvc->>FS: Record handover checkpoint
    Vol->>LogSvc: POST /api/logistics/handover/delivery (verified signature)
    LogSvc->>FS: Mark delivery completed
    LogSvc->>PS: Publish event: "pickup.completed" (portions, kg, donor_id, ngo_id)

    PS->>AS: Push event: "pickup.completed"
    AS->>AS: Compute impact metrics (meals=portions, kg=portions*0.4, CO2e=kg*2.5)
    AS->>FS: Update aggregated impact counters (atomic increment)
    AS->>FS: Recalculate Donor & Volunteer Reliability Scores
    AS->>BQ: Stream row to BigQuery partitioned impact_logs table
```

---

## 4. Architectural Justifications for Managed Cloud Primitives

| Component | Choice | Alternative Considered | Technical Justification |
| :--- | :--- | :--- | :--- |
| **Microservice Runtime** | **Google Cloud Run (v2)** | GKE (Kubernetes), Compute Engine VM | Microservices scale automatically from 0 to hundreds of instances based on HTTP/PubSub traffic. Billed per 100ms of CPU execution time, meaning $0 idle cost during off-peak hours (e.g. 2 AM–6 AM). Container packaging guarantees identical execution between local Docker and production. |
| **Asynchronous Bus** | **Cloud Pub/Sub (Push)** | Kafka, RabbitMQ | Fully managed, zero-ops event streaming with 99.95% SLA. Push subscriptions convert event fanouts into standard HTTPS calls directly into Cloud Run endpoints, eliminating the need to run persistent consumer listener daemon pools. |
| **Delayed Escalation** | **Google Cloud Tasks** | Celery + Redis, Quartz | Offer response timeouts (3 to 15 minutes) require delayed point-in-time invocation. Running Celery requires a dedicated Redis cluster. Cloud Tasks provides serverless, rate-limited, deduped HTTP dispatch at a specific timestamp with automatic retries. |
| **Operational Database**| **Cloud Firestore (Native)**| Cloud SQL (PostgreSQL), MongoDB Atlas | Sub-millisecond reads, native geospatial support, and client SDK `onSnapshot()` listeners enable live real-time UI updates (e.g. fresh food disappearing the second another NGO claims it) without WebSockets or polling servers. |
| **Analytical Warehouse**| **Google BigQuery** | PostgreSQL read replica | Massive streaming insert capability for audit and telemetry logs. Serverless SQL engine allows instant forecasting aggregations across years of donation trends without impacting operational OLTP transactions. |
| **Scheduled Jobs** | **Google Cloud Scheduler** | Cron on VM, Celery Beat | Cloud Scheduler triggers the `expiry-job` endpoint over HTTPS with OIDC service account authentication every 5 minutes to sweep expired listings. |
| **AI Perception** | **Google Gemini 1.5 Flash** | Custom YOLO on GPU | Ultra-fast multimodal model capable of identifying food freshness, portion sizing, packaging integrity, and contamination flags in < 1 second. Fallback table ensures zero availability impact if network is partitioned. |

---

## 5. Fault Tolerance, Idempotency & Dead Letter Strategy

1. **Idempotency Guarantees**:
   Every message published to Cloud Pub/Sub contains a unique `event_id`. Microservice endpoints track processed `event_id` keys in Firestore with a 7-day TTL. Duplicate events (a known property of at-least-once message brokers) are acknowledged immediately without re-triggering business logic.
2. **Dead-Letter Topics (DLQ)**:
   Every Cloud Pub/Sub subscription defines a `dead_letter_policy` routed to `foodbridge-dead-letter`. If an endpoint returns HTTP 5xx or times out 5 consecutive times with exponential backoff, the message is sequestered for human inspection, and a Cloud Monitoring alert is dispatched.
3. **Graceful AI Degradation**:
   When the Gemini API is unreachable, times out, or when running in local development mode without GCP credentials, `vision.py` automatically activates the deterministic rule engine. The engine computes food category heuristics, portions, and shelf life based on safe temperature baselines.

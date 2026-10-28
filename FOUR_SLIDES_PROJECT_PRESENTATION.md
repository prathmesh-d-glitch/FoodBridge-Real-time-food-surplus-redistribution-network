# FoodBridge: Presentation Part 1 (Slides 01 – 04)
> **Comprehensive Presentation Guide, Slide Content & Technical Talking Track**  
> **Course**: Cloud Computing Project | **Evaluation Target**: AWS Serverless Architecture (`ap-south-1` Mumbai)  
> **Project Team Members**:
> - **Prathmesh Dubey** (Roll No: `2023BCS-049`)
> - **Aksh Dhingra** (Roll No: `2023BCS-006`)
> - **Gaurav Dewani** (Roll No: `2023BCS-021`)

---

## Executive Overview of Your Presentation Section

This section covers the foundational narrative of the FoodBridge project:
1. **Slide 01**: Title, project team credentials, and high-level AWS cloud architecture summary.
2. **Slide 02**: Problem breakdown — the perishable food safety window (FSSAI) and why traditional manual systems fail.
3. **Slide 03**: The end-to-end 4-stage operational pipeline (Post → Inspect → Match → Route) centered around the live geospatial map.
4. **Slide 04**: Architectural mapping of operational requirements to serverless AWS services.

---

# SLIDE 01: Project Title & Cloud Architecture Overview

### Slide Visual Content

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  FoodBridge: Real-Time Food Surplus Redistribution Network                             │
│  Serverless Cloud Architecture on AWS (ap-south-1 Mumbai) - Project Evaluation        │
│                                                                                        │
│  PROJECT TEAM MEMBERS                                                                  │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐ │
│  │ Prathmesh Dubey         │  │ Aksh Dhingra            │  │ Gaurav Dewani           │ │
│  │ Roll No: 2023BCS-049    │  │ Roll No: 2023BCS-006    │  │ Roll No: 2023BCS-021    │ │
│  └─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘ │
│                                                                                        │
│  PROJECT OVERVIEW & CORE CLOUD HIGHLIGHTS                                              │
│  FoodBridge is an automated, event-driven serverless platform built on AWS to rescue   │
│  cooked surplus food within the strict 3–4 hour FSSAI perishable window. Manual        │
│  coordination is replaced with real-time WebSocket push updates, AI-assisted computer  │
│  vision photo inspection, and 2-Opt TSP route optimization.                            │
│                                                                                        │
│  • Target Cloud: Amazon Web Services (ap-south-1 Mumbai Region)                        │
│  • Infrastructure as Code: AWS CDK (67 serverless resources deployed in ~65s)         │
│  • Core Stack: API Gateway (HTTP + WebSocket), AWS Lambda (ARM64 Node.js/Python),       │
│                DynamoDB Streams, Amazon SNS                                            │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Information Breakdown

* **Project Identity**:
  * **Title**: FoodBridge: Real-Time Food Surplus Redistribution Network.
  * **Cloud Deployment Context**: AWS Asia Pacific (Mumbai) region (`ap-south-1`).
  * **Team Credits**:
    * **Prathmesh Dubey** — Roll No: `2023BCS-049`
    * **Aksh Dhingra** — Roll No: `2023BCS-006`
    * **Gaurav Dewani** — Roll No: `2023BCS-021`

* **The Problem FoodBridge Solves**:
  * India wastes ~70 million tonnes of food annually while over 190 million people experience nutritional insecurity.
  * In commercial venues (hotels, banquet halls, wedding events, corporate cafeterias), vast quantities of edible cooked food remain after meal services.
  * The fundamental bottleneck is not lack of food or lack of shelters — it is the **rapid decay window** governed by food safety standards (FSSAI).

* **Cloud Architecture Highlights**:
  * **Zero Idle Servers**: No continuously billed virtual machines (`EC2`), no provisioned database instances (`RDS`), and no idle `NAT Gateways`.
  * **ARM64 Graviton2 Compute**: Lambda microservices run on ARM64 architecture, providing a **34% better price-to-performance ratio** over x86.
  * **Event-Driven Push Mesh**: State transitions in DynamoDB immediately stream to downstream consumers without continuous polling.
  * **Single-Command IaC**: AWS CDK synthesizes CloudFormation templates, building all 67 serverless resources in approximately **65 seconds**.

---

### Speaker Script & Talking Points (Slide 01)

> *"Good morning, examiners and evaluators. I am presenting the architecture and core design of **FoodBridge: A Real-Time Food Surplus Redistribution Network**, developed by Prathmesh Dubey, Aksh Dhingra, and Gaurav Dewani.
>
> FoodBridge is an automated, event-driven serverless application deployed in the AWS Mumbai region (`ap-south-1`). It connects large-scale food donors—such as hotels, wedding banquet halls, and caterers—with nearby verified NGO shelters and volunteer drivers to rescue edible cooked food before it spoils.
>
> From a cloud computing perspective, FoodBridge replaces traditional manual spreadsheets and phone calls with an elastic, serverless pipeline: Amazon API Gateway for HTTP and WebSockets, AWS Lambda on 64-bit ARM Graviton2 compute, Amazon DynamoDB with Change Data Capture streams, and Amazon SNS for real-time dispatch alerts. The entire infrastructure is managed through code via AWS CDK, provisioning 67 cloud resources in under 65 seconds with zero idle hosting cost."*

---

# SLIDE 02: Why Food Redistribution Breaks Down

### Slide Visual Content

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  Why Food Redistribution Breaks Down                                                   │
│  The food is ready. The clock is ticking.                                              │
│                                                                                        │
│  • Scattered reports across calls and WhatsApp.        ┌─────────────────────────────┐ │
│  • Static spreadsheets lack real-time visibility.      │ 🕒 Critical Time Window     │ │
│  • Cooked meals spoil within a 3–4 hour FSSAI window.  │ Cooked meals spoil within a │ │
│  • Blind dispatch requires manual phone coordination.  │ strict 3–4 hour FSSAI       │ │
│  • Requires instant push updates and auto-scaling.     │ safety window.              │ │
│                                                        └─────────────────────────────┘ │
│                                                        ┌─────────────────────────────┐ │
│                                                        │ [ Food Rescue Banquet Photo ]││
│                                                        │ Commercial buffet surplus   │ │
│                                                        │ waiting for redistribution  │ │
│                                                        └─────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Information Breakdown

#### 1. The Operational Failure Points
* **Scattered Reports**:
  * Donors notify contacts using informal WhatsApp messages, SMS, and ad-hoc phone calls.
  * Information is siloed across personal chats; there is no centralized, real-time ledger of surplus availability.
* **Static Spreadsheets & Zero Live Visibility**:
  * Relief coordinators and NGOs work from offline spreadsheets or static lists that become obsolete minutes after being compiled.
  * Commanders and dispatchers cannot see where surplus food exists *right now*.
* **The Perishable Clock (FSSAI Food Safety Standards)**:
  * Cooked foods are high-risk perishable items subject to microbiological bacterial growth (e.g., *Staphylococcus aureus*, *Bacillus cereus*).
  * Under **FSSAI and Codex Alimentarius guidelines**, hot cooked food held at ambient temperatures must be distributed and consumed within **3 to 4 hours** of preparation.
  * If food has not reached beneficiaries within this window, it must be condemned and discarded to prevent foodborne illness outbreaks.
* **Blind Dispatch**:
  * Which volunteer driver is free, has thermal hot-holding boxes, and is close enough to collect and deliver before the deadline?
  * Currently answered by frantically calling drivers one by one while food temperature drops.

#### 2. Spoilage Standards Matrix (FSSAI / Codex Alimentarius)

| Food Category | Hot-Hold (>60°C) | Ambient Storage | Refrigerated (<5°C) | Frozen (<-18°C) |
| :--- | :---: | :---: | :---: | :---: |
| **Cooked Meals (Rice, Gravy, Daal)** | **4 Hours** | **3 Hours** | 24 Hours | 72 Hours |
| **Bakery & Bread** | 6 Hours | 36 Hours | 48 Hours | 168 Hours |
| **Raw Produce (Fruits, Veg)** | 4 Hours | 24 Hours | 72 Hours | 168 Hours |
| **Dairy Items** | 2 Hours | 3 Hours | 12 Hours | 48 Hours |

#### 3. How the Problem Dictates Cloud Architecture
* **Real-Time Push, Not Refresh**: A 30-minute delay in viewing a listing means 15–20% of the food's safe life is already lost. Dashboards must receive instant push updates.
* **Elastic Surge Handling**: Zero donations for 5 days, followed by 500 kg of surplus arriving simultaneously at 11:30 PM from three wedding receptions. The cloud backend must scale from zero to peak instantaneously without manual server provisioning.
* **High Availability**: During severe crises or festival surges, the platform cannot go down for operating system patches or server maintenance.

---

### Speaker Script & Talking Points (Slide 02)

> *"Moving to Slide 2: Why does food redistribution break down today? The issue is never a shortage of food or a lack of willing volunteers. The problem is that **the food is ready, but the information is not**.
>
> Today, when a banquet hall has 100 surplus meals at the end of an event, the chef posts in a WhatsApp group or calls contacts. Meanwhile, shelter coordinators see static spreadsheets that do not reflect what is edible right now.
>
> The most critical factor highlighted on this slide is the **Critical Time Window**. According to FSSAI food safety regulations, hot cooked meals have a strict consumption window of only 3 to 4 hours. Manual dispatch over phone calls simply cannot verify routes, driver equipment, and shelter intake capacity before that window closes.
>
> This operational challenge directly shaped our cloud architecture: because food safety decays every minute, the system requires sub-second push updates, automated time-feasibility filtering, and an elastic backend that scales dynamically during evening banquet surges."*

---

# SLIDE 03: FoodBridge: One Operational Picture

### Slide Visual Content

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  FoodBridge: One Operational Picture                                                   │
│  Report, inspect, match, route, and track on one live map.                             │
│                                                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ 1. POST          │  │ 2. INSPECT       │  │ 3. MATCH         │  │ 4. ROUTE        │ │
│  │ Pin location,    │  │ AI analyzes      │  │ 6-factor         │  │ 2-Opt TSP       │ │
│  │ auto-compute     │  │ photos for       │  │ composite score  │  │ optimization    │ │
│  │ FSSAI safe       │  │ hygiene and      │  │ ranks NGOs.      │  │ with live CO2e  │ │
│  │ window.          │  │ portions.        │  │                  │  │ tracking.       │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │ [ Live Redistribution Map - Leaflet / OpenStreetMap ]                            │  │
│  │  • Green Pins: Active food listings with dynamic countdown clocks.               │  │
│  │  • Blue Pins: Verified NGO shelters with capacity intake meters.                 │  │
│  │  • Orange Polylines: In-transit volunteer couriers on optimized TSP routes.     │  │
│  │  • Right Sidebar: Live network entities & real-time telemetry.                  │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Information Breakdown

FoodBridge structures the entire food rescue lifecycle into a unified, 4-stage automated pipeline:

#### Stage 1: POST (Donor Listing Creation & Freshness Clock)
* **Geospatial Pinning**: The donor logs in, GPS auto-detects their facility, and the location is encoded into a **Precision-6 Geohash** (bounding box ~1.2 km × 0.6 km) for rapid spatial indexing.
* **Automatic Expiration Computation**: The system calculates the safe deadline mathematically:
  $$\text{safe\_until} = \text{prepared\_at} + \text{SHELF\_LIFE\_HOURS}[(\text{category}, \text{storage\_condition})]$$
  For example: Cooked Meals + Hot Hold (`>60°C`) = Preparation Time + 4.0 Hours.
* **Live Freshness Clock**: A real-time countdown timer begins decrementing on all connected client dashboards.

#### Stage 2: INSPECT (Multimodal AI Computer Vision Analysis)
* **Vision Model**: Uses Google Gemini 1.5 Flash / AWS Rekognition to inspect uploaded food photos.
* **Automated Extraction**:
  1. **Food Category**: Validates whether the image matches the selected category (e.g., Cooked Meals, Bakery, Produce).
  2. **Portion Estimation**: Computes estimated meal portions from tray dimensions and food density.
  3. **Hygiene & Safety Flags**: Inspects storage containers (e.g., *"Stainless steel thermal hot-holding container verified"*, *"Sealed packaging confirmed"*).
* **Deterministic Fallback**: If the vision API experiences rate limits or network issues, the system automatically falls back to deterministic FSSAI category lookup tables with zero user-facing errors.

#### Stage 3: MATCH (Hard Spoilage Filter + 6-Factor Composite Scoring)
* **Step 3A: Hard Spoilage Filter (Binary Disqualification)**:
  Before scoring, candidate NGOs are filtered out if physical delivery is impossible before food safety expires:
  $$\text{Required Time} = \text{Travel ETA} + 15\text{ min (loading buffer)}$$
  $$\text{Available Time} = \text{Remaining Shelf Life} - 30\text{ min (safety margin)}$$
  $$\text{IF } \text{Required Time} > \text{Available Time} \implies \mathbf{DISQUALIFIED}$$
* **Step 3B: 6-Factor Composite Scoring Algorithm**:
  Eligible NGOs are ranked from Rank 1 to Rank $N$ using a weighted mathematical formula:
  $$\text{Score} = 0.30 \cdot F_{\text{time}} + 0.25 \cdot F_{\text{prox}} + 0.15 \cdot F_{\text{cap}} + 0.10 \cdot F_{\text{diet}} + 0.15 \cdot F_{\text{rel}} + 0.05 \cdot F_{\text{urg}}$$
  * $F_{\text{time}}$: Travel time feasibility margin.
  * $F_{\text{prox}}$: Proximity score based on normalized Haversine distance ($d \le 15\text{ km}$).
  * $F_{\text{cap}}$: Capacity match between donor kg and shelter intake capacity.
  * $F_{\text{diet}}$: Dietary compatibility (Vegetarian, Vegan, Non-Veg, Halal).
  * $F_{\text{rel}}$: Historical NGO reliability rating (successful handovers vs. timeouts).
  * $F_{\text{urg}}$: Current shelter hunger queue urgency.
* **Cascading Offers**: The offer is dispatched to the **Rank 1 NGO** with a dynamic countdown timeout:
  $$\tau = \text{clamp}(0.10 \times \text{remaining shelf life}, 3\text{ min}, 15\text{ min})$$
  If Rank 1 declines or times out, the system automatically cascades the offer to Rank 2.

#### Stage 4: ROUTE & TRACK (2-Opt TSP Dispatch, Temperature Verification & Impact)
* **2-Opt Travelling Salesperson Problem (TSP) Optimization**:
  * Constructs an initial greedy tour respecting hard pickup deadlines.
  * Iteratively swaps edge pairs ($i, j$) to eliminate overlapping routes and minimize total transit kilometers.
* **Food Safety Handover Audit**:
  * The courier records container temperature upon pickup and delivery.
  * Validates thermal safety compliance: **Hot-hold must be $>60^\circ\text{C}$**; **Cold-chain must be $<5^\circ\text{C}$**.
  * Digital signature verification logged for tamper-proof compliance.
* **Environmental Impact Tracking**:
  * **Meals Saved**: $\text{kg} \times 2.8\text{ meals/kg}$
  * **$\text{CO}_2\text{e}$ Avoided**: $\text{kg} \times 2.5\text{ kg CO}_2\text{e/kg}$ (IPCC food waste emission factor)
  * Generates an automated, downloadable CSR ESG PDF Certificate with verifiable cryptographic hash.

---

### Speaker Script & Talking Points (Slide 03)

> *"On Slide 3, we see FoodBridge's solution: **One Operational Picture**. All stakeholders—donors, shelter managers, and volunteer drivers—collaborate on a single live geospatial dashboard.
>
> The redistribution pipeline operates in four automated steps:
> 1. **Post**: The donor pins their kitchen GPS and selects storage conditions. Our FSSAI engine instantly computes the exact `safe_until` timestamp, launching a real-time Freshness Clock.
> 2. **Inspect**: As the photo is uploaded, computer vision AI analyzes the image, validating the food category, estimating portions, and confirming hygiene standards such as thermal containers.
> 3. **Match**: Our matching engine runs two checks. First, a hard spoilage filter that disqualifies any NGO that cannot be reached before safe expiration minus a 30-minute buffer. Second, our explainable 6-Factor Composite Score evaluates time feasibility, proximity, capacity, dietary preferences, reliability, and urgency to send an offer to the highest-ranked NGO with a cascading timeout.
> 4. **Route & Track**: Once accepted, our 2-Opt TSP algorithm optimizes the volunteer's driving itinerary to minimize travel time. At delivery, couriers log temperature verification—ensuring hot food stayed above 60°C—and the system increments live impact metrics: meals rescued and greenhouse gases avoided."*

---

# SLIDE 04: Why Serverless on AWS?

### Slide Visual Content

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  Why Serverless on AWS?                                                                │
│  Mapping operational requirements to AWS cloud services.                               │
│                                                                                        │
│  ┌────────────────────────────────────────┐  ┌───────────────────────────────────────┐ │
│  │ Operational Requirement                │  │ Operational Requirement               │ │
│  │ Real-time push                         │  │ Static PWA hosting                    │ │
│  │ API Gateway WebSocket                  │  │ Amazon S3                             │ │
│  └────────────────────────────────────────┘  └───────────────────────────────────────┘ │
│                                                                                        │
│  ┌────────────────────────────────────────┐  ┌───────────────────────────────────────┐ │
│  │ Operational Requirement                │  │ Operational Requirement               │ │
│  │ Zero-idle compute                      │  │ IaC repeatability                     │ │
│  │ AWS Lambda (ARM64)                     │  │ AWS CDK                               │ │
│  └────────────────────────────────────────┘  └───────────────────────────────────────┘ │
│                                                                                        │
│  ┌────────────────────────────────────────┐  ┌───────────────────────────────────────┐ │
│  │ Operational Requirement                │  │ Architectural Outcome                 │ │
│  │ Low-latency NoSQL                      │  │ Fully Managed Cloud Architecture      │ │
│  │ DynamoDB On-Demand                     │  │ Zero server administration with       │ │
│  │                                        │  │ pay-per-use efficiency                │ │
│  └────────────────────────────────────────┘  └───────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Information Breakdown

Every operational requirement in FoodBridge maps directly to a cloud computing concept and an AWS managed serverless primitive:

| # | Operational Requirement | Cloud Computing Concept | AWS Service Selected | Implementation in FoodBridge |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Real-Time Push** | Event-Driven Ingress & State Push | **Amazon API Gateway WebSocket** | Maintains bi-directional socket connections; broadcasts state changes in $<150\text{ ms}$; replaces wasteful HTTP polling. |
| **2** | **Static PWA Hosting** | Global Edge Storage | **Amazon S3 (+ CloudFront)** | Hosts the pre-compiled React 18 / Vite / TypeScript single-page application; delivers assets with zero server maintenance. |
| **3** | **Zero-Idle Compute** | Serverless Elasticity & Micro-Billing | **AWS Lambda (ARM64 Graviton2)** | Runs Python 3.12 / Node.js 22 microservices; bills exclusively per millisecond of execution; scales to zero when idle ($0 base cost). |
| **4** | **IaC Repeatability** | Infrastructure as Code (IaC) | **AWS CDK (Cloud Development Kit)** | Defines all 67 resources programmatically in TypeScript; guarantees clean, reproducible deployments with `cdk deploy`. |
| **5** | **Low-Latency NoSQL** | Managed Elastic Data Store | **Amazon DynamoDB (On-Demand)** | Provides single-digit millisecond reads/writes; automatic capacity scaling with zero capacity planning; Change Data Capture via DynamoDB Streams. |
| **6** | **Architectural Outcome** | **Fully Managed Cloud Architecture** | **Regional Multi-AZ Resilience** | High availability built into the cloud fabric across 3 availability zones in `ap-south-1`; zero OS patching, zero downtime. |

#### Architectural Deep-Dive on Key AWS Decisions

1. **Why API Gateway WebSockets over HTTP Polling?**:
   * *Traditional Polling*: Clients query `GET /listings` every 3 seconds. For 1,000 active viewers, this generates **1.2 million idle requests per hour**, consuming bandwidth, battery, and server invocations.
   * *FoodBridge WebSockets*: The server pushes a notification only when a database state change occurs. Reduces idle requests from **1,200 to 0 per viewer-hour**, reducing backend compute overhead by 99.8%.

2. **Why ARM64 Graviton2 for AWS Lambda?**:
   * ARM64 architecture delivers up to **34% better price/performance** compared to x86-64 instances.
   * Faster cold-start initialization times for Python and Node.js microservice runtimes.

3. **Why DynamoDB On-Demand Billing?**:
   * Food surplus donations are unpredictable and bursty (e.g., zero traffic in the afternoon, sudden spikes at 11:00 PM).
   * Provisioned Capacity Units (RCUs/WCUs) would result in overpaying during quiet hours or throttling during surges.
   * On-Demand billing charges strictly per read and write request, aligning infrastructure cost directly with rescue activity.

4. **Why AWS CDK for Infrastructure as Code?**:
   * Avoids fragile, error-prone manual console configuration.
   * Synthesizes CloudFormation with verified IAM least-privilege security roles generated automatically.
   * Entire stack can be torn down completely (`npx cdk destroy`) with zero residual billing.

---

### Speaker Script & Talking Points (Slide 04)

> *"In Slide 4, we examine how our functional requirements dictated our cloud technology selection on AWS.
>
> 1. **Real-Time Push via API Gateway WebSocket**: Polling an API every 3 seconds would produce 1,200 idle requests per viewer-hour. By using managed WebSockets, clients maintain a single lightweight connection, and updates are pushed instantly when database state changes—dropping idle network requests to absolute zero.
> 2. **Static PWA Hosting on Amazon S3**: Our client application is an offline-capable React Progressive Web App. S3 provides high availability and fast edge loading without managing web servers.
> 3. **Zero-Idle Compute with AWS Lambda on ARM64**: Because surplus food rescue is highly bursty, traditional EC2 instances would sit idle 80% of the day while accruing hourly costs. Lambda scales to zero when there is no traffic and scales up instantaneously during peak rushes, while ARM64 Graviton2 processors provide 34% better price-performance.
> 4. **IaC Repeatability with AWS CDK**: Rather than manually configuring cloud resources in the AWS console, all 67 resources are defined programmatically using TypeScript in AWS CDK. The entire environment deploys in ~65 seconds.
> 5. **Low-Latency NoSQL with DynamoDB On-Demand**: DynamoDB delivers single-digit millisecond performance for geospatial queries and listing updates. On-Demand pricing means we never pay for idle capacity.
>
> **The Architectural Outcome**: FoodBridge achieves a fully managed, production-grade cloud architecture that requires zero server administration, delivers multi-AZ fault tolerance, and operates with maximum pay-per-use cost efficiency."*

---

## Technical Examiner Q&A Guide (Prepared for Your 4 Slides)

### Q1: Why did you choose AWS Serverless instead of running Docker containers on EC2 or ECS?
**Answer**:
> *"Food redistribution is inherently sporadic. Commercial venues donate food after specific banquet events or at closing time. An EC2 instance or ECS cluster incurs 24/7 hourly compute and load-balancer costs even when zero food is being donated. With AWS Lambda, API Gateway, and DynamoDB On-Demand, FoodBridge scales to zero when idle, meaning our idle hosting cost is exactly **$0.00/month**. When a sudden surge occurs, serverless scales horizontally within milliseconds without manual intervention."*

### Q2: How does the system enforce FSSAI food safety compliance if an NGO claims food late?
**Answer**:
> *"We enforce food safety at two distinct layers:
> First, our **Hard Spoilage Filter** in the matching algorithm runs a strict time-feasibility calculation. If the sum of travel ETA and handover loading time exceeds the remaining safe shelf-life minus a 30-minute safety buffer, the candidate NGO is mathematically disqualified before scoring begins.
> Second, we employ an automated background **Expiry Job** that runs every 60 seconds. Any listing that passes its `safe_until` timestamp without being claimed is automatically marked `EXPIRED` in DynamoDB and removed from all active feeds."*

### Q3: What is the benefit of DynamoDB Streams in your architecture?
**Answer**:
> *"DynamoDB Streams provides real-time Change Data Capture (CDC). When a listing or offer status changes in the `foodbridge-listings` table, DynamoDB emits an ordered event stream. This immediately triggers our downstream Lambda functions—which calculate match rankings and publish to the WebSocket broadcaster—completely decoupling our API ingestion from our dispatch and notification workflows."*

### Q4: How does 2-Opt TSP optimization benefit the volunteer courier?
**Answer**:
> *"In a multi-stop food rescue scenario, picking up from multiple donors and delivering to different shelters creates route conflicts. A naive route could cause a driver to zigzag across the city, violating the 3-hour food safety deadline. The 2-Opt heuristic takes an initial route and iteratively swaps edge pairs to eliminate crossings, reducing total mileage and ensuring deliveries occur well within the FSSAI deadline."*

---

## Summary Checklist for Your Presentation

- [x] **Slide 01**: Team details confirmed (Prathmesh, Aksh, Gaurav), AWS `ap-south-1` region, 67 resources, ~65s CDK deployment.
- [x] **Slide 02**: Problem context (scattered WhatsApp reports, static spreadsheets, blind dispatch, 3–4 hour FSSAI perishable clock, auto-scaling requirements).
- [x] **Slide 03**: 4-Stage pipeline (1. Post + FSSAI clock, 2. Inspect + AI vision, 3. Match + 6-factor score + cascade, 4. Route + 2-Opt TSP + CO2e tracking), Live map UI explained.
- [x] **Slide 04**: All 5 AWS operational mappings detailed (API Gateway WebSockets, S3, Lambda ARM64, CDK, DynamoDB On-Demand) and the final Architectural Outcome.
- [x] **Talking Track**: Scripted speech provided for each of the 4 slides with examiner defense Q&A.

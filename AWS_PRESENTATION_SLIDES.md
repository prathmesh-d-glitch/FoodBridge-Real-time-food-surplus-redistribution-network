# FoodBridge — AWS Cloud Computing Presentation Slides & Master Prompt

> **Project Title**: FoodBridge — Real-Time Food Surplus Redistribution Network  
> **Course**: Cloud Computing Project  
> **Target Cloud**: Amazon Web Services (AWS serverless stack in `ap-south-1` Mumbai)

---

# SECTION 1: MASTER AI GENERATION PROMPT

*(Copy and paste this into Gamma, Beautiful.ai, Claude, or ChatGPT to generate or rebuild slides)*

```text
Create a 10-slide presentation for a Cloud Computing project: "FoodBridge: Real-Time Food Surplus Redistribution Network", presented as a serverless application deployed on AWS (ap-south-1). 

Strictly use only the project's actual features and architecture:
- Problem: Cooked surplus food spoils in 3–4 hours (FSSAI). Manual calls and spreadsheets are too slow.
- Solution: Automated 5-stage pipeline: Post -> Inspect (AI Photo) -> Match (6-Factor Composite Score) -> Route (2-Opt TSP) -> Verify & Impact (CO2e, Meals saved).
- AWS Architecture: Amazon S3 (PWA hosting & photo store), API Gateway (HTTP REST + WebSocket Push), AWS Lambda (ARM64 Node.js/Python), DynamoDB (4 tables + Streams), Amazon SNS (Alerts), and AWS CDK.
- Data Layer: 4 DynamoDB on-demand tables (foodbridge-listings, foodbridge-offers, foodbridge-routes, foodbridge-connections with TTL).
- Key Cloud Findings: WebSocket push eliminating 1,200 idle requests/viewer-hour vs polling; API Gateway 25 rps throttling protecting Lambda and DynamoDB (0 server errors across 510 load-test requests).
- IaC: AWS CDK single-command deployment (npx cdk deploy, 67 resources).

Format the output across 10 clean slides matching the technical style of the reference deck with exact tables, counts, flows, and CLI commands.
```

---

# SECTION 2: THE 10 SLIDES (FULL CONTENT)

---

### Slide 01 / 10
## Why Food Redistribution Breaks Down
#### The food is ready. The clock is ticking.

* **Scattered reports**  
  Calls, messages and WhatsApp posts reach different volunteers. Nobody holds one live list.
* **No live picture**  
  NGOs and shelters see an old spreadsheet, not what edible food is available right now.
* **Perishable clock**  
  Cooked meals spoil within a strict 3–4 hour FSSAI window. Manual coordination is too slow.
* **Blind dispatch**  
  Which volunteer is free, has the right containers, and is nearest? Usually answered by phone.

#### WHAT THE SYSTEM MUST DO, AND WHY IT SHAPES THE CLOUD CHOICES
* **Show changes instantly** → Real-time push, not refresh.
* **Stay up in a crisis** → Managed, highly available services.
* **Scale with the surplus** → Quiet for hours, then sudden banquet surges.

`FoodBridge · Cloud Computing project 01 / 10`

---

### Slide 02 / 10
## FoodBridge: One Operational Picture
#### Report, inspect, match, route and track, on one live map.

* **1 Post**  
  Donor pins the location, quantity, storage type, and photo. FSSAI `safe_until` auto-computes.
* **2 Inspect**  
  AI photo analysis checks food category, estimated portions, and hygiene flags.
* **3 Match**  
  6-factor composite score ranks candidate NGOs with a hard time-feasibility check.
* **4 Route & Track**  
  2-Opt TSP optimized volunteer route, temperature-verified handover, and live CO2e analytics.

*Live map: surplus food status, NGO shelters, and volunteer transit routes.*

`FoodBridge · Cloud Computing project 02 / 10`

---

### Slide 03 / 10
## Why Serverless on AWS?
#### Each requirement maps to a cloud concept and a service.

| Requirement | Cloud concept | How FoodBridge uses it |
| :--- | :--- | :--- |
| **Spiky demand** | Elasticity | Lambda and DynamoDB on-demand scale up and down with meal rushes |
| **Must stay up** | Managed high availability | Regional multi-AZ services (`ap-south-1`), no servers to patch |
| **Instant updates** | Event-driven design | WebSocket push plus DynamoDB Streams for freshness clocks |
| **Controlled actions** | Identity and least privilege | JWT sign-in roles (Donor, NGO, Volunteer), one IAM role per function |
| **Small budget** | Pay per use | No hourly servers: no EC2, NAT gateway or RDS ($0 when idle) |
| **Repeatable setup** | Infrastructure as code | AWS CDK: one command builds all 67 resources |

`FoodBridge · Cloud Computing project 03 / 10`

---

### Slide 04 / 10
## System Architecture: Serverless and Event-Driven

* **CLIENT**: Browser app (React PWA, Vite, TypeScript, Leaflet map) — Donor, NGO, Volunteer, Admin
* **ACCESS**: Amazon S3 (Static site hosting) + User sign-in (JWT token, roles)
* **API**: 
  * API Gateway: HTTP (JWT authorizer, 25 rps throttling)
  * API Gateway: WebSocket (Live push to dashboards)
* **COMPUTE**: AWS Lambda x3 (`api`, `ws-connect`, `alert-stream`) + AI photo analysis (Labels food category and portion count)
* **DATA**: DynamoDB (4 tables + Streams) + S3 photos (Private bucket) + Amazon SNS (Email/SMS alerts)
* **OPERATIONS**: CloudWatch logs, metrics and AWS CDK

#### DATA FLOW
1. App loads from S3; user signs in.
2. API Gateway checks the JWT.
3. Lambda runs FSSAI safety calculation and AI photo inspection.
4. State saved to DynamoDB; photos to private S3.
5. DynamoDB Stream triggers alert Lambda → matching engine → SNS email.
6. Lambda pushes live updates over WebSocket to connected clients.

`FoodBridge · Cloud Computing project 04 / 10`

---

### Slide 05 / 10
## 6 AWS Services, Verified in the Account
#### Counts below come from AWS CLI calls on the deployed stack (ap-south-1).

* **Amazon S3**  
  Static site hosting and private food photo store  
  `2 buckets`
* **API Gateway**  
  HTTP API with JWT authorizer, plus WebSocket  
  `2 APIs, 8 routes`
* **AWS Lambda**  
  Business logic, 2-Opt routing, sockets, stream alerts  
  `3 fns, nodejs22.x/python3.12, arm64`
* **DynamoDB**  
  Listings, offers, routes, connections  
  `4 tables, on-demand`
* **Amazon SNS**  
  Pickup alerts and cascading timeout notifications  
  `1 topic + filter`
* **AWS IAM**  
  Least-privilege role per function  
  `3 scoped execution roles`

```bash
$ aws lambda list-functions  ·  aws dynamodb describe-table
```

`FoodBridge · Cloud Computing project 05 / 10`

---

### Slide 06 / 10
## One Surplus Rescue, Seven Steps
#### What happens when a donor posts 40 kg of surplus food with a photo.

1. **Sign in**: Donor signs in and receives a signed JWT.
2. **POST /listings**: Form payload sent with photo; API Gateway verifies JWT.
3. **Lambda validates**: FSSAI rule computes `safe_until`; stores photo in private S3.
4. **AI photo analysis**: Computer vision inspects food type and portions.
5. **Saved in DynamoDB**: Listing saved with status `"available"`.
6. **DynamoDB Stream triggers Lambda**: 6-factor algorithm ranks NGOs; publishes alert to SNS.
7. **WebSocket push**: Every open NGO feed and live map updates instantly.

*AI result: Cooked Meals 98%, Portions ~80, Hot-Hold Verified*  
*Test photo: Buffet banquet surplus.*

`FoodBridge · Cloud Computing project 06 / 10`

---

### Slide 07 / 10
## Data Layer: DynamoDB Data Model
#### Four on-demand tables, all keyed by id.

* **`foodbridge-listings`** (Key: `id` · Stream: ON)  
  `donorId`, `title`, `category`, `storageCondition`, `quantityKg`, `safeUntil`, `status` (`available` to `completed`), `geohash`, `photoKey`, `aiLabels`
* **`foodbridge-offers`** (Key: `id`)  
  `listingId`, `ngoId`, `rank`, `compositeScore`, `status` (`offered`, `accepted`, `declined`, `timeout`), `timeoutAt`
* **`foodbridge-routes`** (Key: `id`)  
  `volunteerId`, `stops`, `tspDistanceKm`, `etaMinutes`, `status` (`assigned`, `in_transit`, `completed`), `handoverTemp`
* **`foodbridge-connections`** (Key: `id`)  
  `id` = WebSocket connection ID, `userId`, `role`, `ttl`: expires after 2 hours

> **At scale**: Add a GSI on `status` and `safeUntil`, and geohash prefix filtering for "nearest NGO".

`FoodBridge · Cloud Computing project 07 / 10`

---

### Slide 08 / 10
## WebSocket Push vs Polling
#### Why dashboards update the moment food is posted, without refreshing.

| Metric | Polling (3 s) | WebSocket push |
| :--- | :---: | :---: |
| **Idle requests per viewer-hour** | 1,200 | **0** |
| **Delay before a change shows** | Up to 3 s | **Near-instant (<150 ms)** |
| **Cost grows with** | Viewers × time | Number of actual status changes |

#### KEY FINDING
$$\mathbf{1,200 \longrightarrow 0}$$  
**idle requests per viewer-hour when polling is replaced by push.**  
Protects volunteer phone batteries and prevents wasted Lambda invocations.

`FoodBridge · Cloud Computing project 08 / 10`

---

### Slide 09 / 10
## Load Test: Throttling Protects the Backend
#### 510 real requests from one laptop to the live API (GET /listings).

* **61 ms** median latency at about 62 requests per second
* **0** server errors (5xx) across all 510 requests
* **282 / 300** burst requests rejected by the 25 rps throttle in 0.6 s

*Graph from our AWS account: 429 means Too Many Requests — the throttle working as designed to safeguard database and compute resources.*

`FoodBridge · Cloud Computing project 09 / 10`

---

### Slide 10 / 10
## Infrastructure as Code & Scalability
#### One command builds it, metrics and logs watch it, one command removes it.

```typescript
// infra/lib/stack.ts (excerpt)
const api = new lambda.Function(this, 'ApiFunction', {
  runtime: lambda.Runtime.NODEJS_22_X,
  architecture: lambda.Architecture.ARM_64, ...
});
listings.grantReadWriteData(api); // scoped IAM generated by CDK
```

```bash
$ npx cdk deploy   # 67 resources, ~65 s
$ npx cdk destroy  # remove all
```

* **Repeatable & Tagged**: Stack tagged `Project=foodbridge`. Rebuilt cleanly multiple times during development.
* **Observability**: CloudWatch metrics for API, Lambda, DynamoDB, SNS, WebSocket. Logs kept for 7 days. Dead connections cleaned up on `410 Gone`.

#### How It Scales in future
| Tier | How it scales | What limits us today |
| :--- | :--- | :--- |
| **S3 site** | Effectively unlimited request rate | No CDN yet, so global latency is higher |
| **API Gateway** | Managed; account default is 10,000 rps | Our own throttle: 25 rps, burst 50 |
| **Lambda** | One execution environment per concurrent request | Account quota is 10 concurrent: request an increase |
| **DynamoDB** | On-demand adapts to traffic, billed per request | Scan reads: add a GSI and geohash at scale |
| **WebSocket** | Managed connections | Broadcast loop in one Lambda: use SNS/SQS fanout |
| **SNS** | Managed, high service quotas | India SMS needs DLT registration: email only |

`FoodBridge · Cloud Computing project 10 / 10`

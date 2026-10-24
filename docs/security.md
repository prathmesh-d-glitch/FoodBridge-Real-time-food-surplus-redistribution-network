# FoodBridge: Security, IAM, and Threat Modeling Specification

## 1. Zero Trust Architecture & Principle of Least Privilege (PoLP)

FoodBridge is designed so that no single compromised microservice or client credential can compromise the database or adjacent services. Every identity in the system—whether a browser client, an administrative dashboard, or an internal Cloud Run container—operates under explicitly scoped permissions.

### 1.1. Per-Microservice Cloud IAM Matrix

In standard deployments, using a single shared default Compute Engine service account leads to severe privilege escalation vulnerabilities. FoodBridge provisions **dedicated Service Accounts per microservice** via Terraform:

| Microservice | Dedicated Service Account | IAM Roles Granted | Justification |
| :--- | :--- | :--- | :--- |
| **listing-service** | `sa-listing-svc@...` | `roles/datastore.user`<br/>`roles/pubsub.publisher`<br/>`roles/storage.objectAdmin` | Needs to create listings in Firestore, publish `listing.created`, and store food photos in Cloud Storage. Cannot write to BigQuery or invoke Cloud Tasks directly. |
| **matching-service** | `sa-matching-svc@...` | `roles/datastore.user`<br/>`roles/pubsub.publisher`<br/>`roles/cloudtasks.enqueuer` | Needs to query candidate NGOs, update offer status, and schedule cascading timeout jobs in Cloud Tasks. |
| **notification-service** | `sa-notif-svc@...` | `roles/secretmanager.secretAccessor` | Only requires read access to FCM push keys and SMS API credentials. Operates in read-only mode relative to operational data. |
| **logistics-service** | `sa-logistics-svc@...` | `roles/datastore.user`<br/>`roles/pubsub.publisher` | Writes handover logs and route assignments. |
| **analytics-service** | `sa-analytics-svc@...` | `roles/datastore.user`<br/>`roles/bigquery.dataEditor` | Streams anonymized audit rows to BigQuery; generates CSR certificates. |
| **expiry-job** | `sa-expiry-job@...` | `roles/datastore.user`<br/>`roles/pubsub.publisher` | Periodic sweeper; only has permission to update listing statuses to `EXPIRED`. |

---

## 2. Firestore Security Rules Rationale

FoodBridge enforces security at the data layer using declarative `firestore.rules`. Even if a malicious actor acquires a valid Firebase Auth user token, they cannot read or tamper with unauthorized documents.

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Helper function for user role validation
    function hasRole(role) {
      return request.auth != null && request.auth.token.role == role;
    }
    
    function isAdmin() {
      return hasRole('admin');
    }

    // Listings collection
    match /listings/{listingId} {
      // Anyone authenticated can read active listings
      allow read: if request.auth != null;
      // Only verified Donors and Admins can create listings
      allow create: if (hasRole('donor') && request.resource.data.donor_id == request.auth.uid) || isAdmin();
      // Updates restricted to creator or admin
      allow update: if (hasRole('donor') && resource.data.donor_id == request.auth.uid) || isAdmin();
    }

    // Offers collection
    match /offers/{offerId} {
      // NGOs can only read offers dispatched directly to them
      allow read: if (hasRole('ngo') && resource.data.recipient_id == request.auth.uid) || isAdmin();
      // Only the assigned recipient can accept or decline their offer
      allow update: if hasRole('ngo') && resource.data.recipient_id == request.auth.uid;
    }
    
    // Handover audit logs (Immutability guarantee)
    match /handovers/{handoverId} {
      allow read: if request.auth != null;
      // Once created, handover audit records are tamper-proof and immutable
      allow create: if hasRole('volunteer') || isAdmin();
      allow update, delete: if false; 
    }
  }
}
```

---

## 3. PII Handling & Sensitive Data Protection

FoodBridge handles sensitive contact information for shelter coordinators, volunteers, and donors. The platform adheres to **Data Minimization** and **Privacy by Design**:

1. **Phone Number Masking & Ephemeral Contact Tokens**:
   Direct phone numbers are never exposed in public listing payloads or on the Live Map. When a volunteer is en route, contact is facilitated via an anonymized telephony proxy or masked token.
2. **Geographical Coordinate Blurring on Public Map**:
   The public Live Map displays donor and recipient locations generalized to 3 geohash digits (~150 km) or centroid jittering (±300 meters) until an offer is formally accepted. Precise doorway instructions and gate codes are only revealed to the assigned volunteer after verified acceptance.
3. **Audit Trail Anonymization for BigQuery**:
   Data streamed to BigQuery for ML forecasting and municipal reporting strips all personally identifiable information (donor names, phone numbers, individual volunteer IDs), retaining only categorized metadata (`category`, `dietary_type`, `portions`, `ward_id`, `co2e_saved`).

---

## 4. Abuse, Fraud, and Food Safety Mitigation

Because bad actors could exploit the platform to dump spoiled food or falsely claim donations, multi-layered anti-fraud controls are enforced:

1. **Trust Layer & Tiered Verification**:
   - Every Donor and NGO profile maintains an explicit verification status: `PENDING_VERIFICATION`, `VERIFIED_FSSAI`, or `SUSPENDED`.
   - First-time donors are capped at 30 portions maximum until their first 3 handovers receive positive temperature and packaging ratings from recipient NGOs.
2. **Cold Chain & Hot Hold Verification Checkpoints**:
   - During volunteer pickup, volunteers record the food container temperature via digital thermometer (`measured_temp_celsius`).
   - If cooked food hot-hold is recorded below $60^\circ\text{C}$ after more than 2 hours of transit, the system triggers a **Safety Alert** flag, instructing the recipient NGO to inspect or reheat before serving.
3. **Cryptographic Proof of Handover**:
   - Handover completion requires a dual-confirmation QR handshake: the donor presents a time-based rotating QR code, which the volunteer scans in the PWA. Both timestamps, GPS coordinates, and optional photographic proof are committed to an immutable append-only audit collection.
4. **Rate Limiting & Anti-Sybil Defense**:
   - Ingress endpoints enforce token-bucket rate limiting (60 requests/minute per IP) on Cloud Run using Cloud Armor security policies to prevent scraping or denial-of-service attacks.

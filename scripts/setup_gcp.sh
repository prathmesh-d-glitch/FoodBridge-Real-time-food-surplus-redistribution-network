#!/usr/bin/env bash
# ==============================================================================
# FoodBridge: Google Cloud Platform Bootstrap Script
# Sets up APIs, Artifact Registry, Terraform state bucket, and service accounts.
# ==============================================================================

set -euo pipefail

# Configuration defaults
PROJECT_ID="${1:-${GCP_PROJECT_ID:-}}"
REGION="${2:-${GCP_REGION:-asia-south1}}"

if [ -z "$PROJECT_ID" ]; then
  echo "ERROR: Project ID is required."
  echo "Usage: ./scripts/setup_gcp.sh <PROJECT_ID> [REGION]"
  exit 1
fi

echo "================================================================="
echo " Bootstrapping FoodBridge GCP Project: $PROJECT_ID ($REGION)"
echo "================================================================="

# Set current active project
gcloud config set project "$PROJECT_ID"

echo "--> 1. Enabling essential GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  pubsub.googleapis.com \
  firestore.googleapis.com \
  cloudtasks.googleapis.com \
  cloudscheduler.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  firebase.googleapis.com

echo "--> 2. Creating Artifact Registry Docker repository..."
if ! gcloud artifacts repositories describe foodbridge --location="$REGION" &>/dev/null; then
  gcloud artifacts repositories create foodbridge \
    --repository-format=docker \
    --location="$REGION" \
    --description="FoodBridge microservices container images"
  echo "Created Artifact Registry repository: foodbridge"
else
  echo "Artifact Registry repository already exists."
fi

echo "--> 3. Configuring Docker credential helper..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

echo "--> 4. Setting up Terraform Remote State Bucket..."
TF_STATE_BUCKET="${PROJECT_ID}-tfstate"
if ! gsutil ls -b "gs://${TF_STATE_BUCKET}" &>/dev/null; then
  gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://${TF_STATE_BUCKET}"
  gsutil versioning set on "gs://${TF_STATE_BUCKET}"
  echo "Created Terraform state bucket: gs://${TF_STATE_BUCKET}"
else
  echo "Terraform state bucket already exists."
fi

echo "--> 5. Creating Deployer Service Account for CI/CD..."
SA_NAME="foodbridge-deployer"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null; then
  gcloud iam service-accounts create "$SA_NAME" \
    --display-name="FoodBridge GitHub Actions Deployer"
  echo "Created service account: $SA_EMAIL"
fi

# Assign least privilege roles required for deployment
ROLES=(
  "roles/run.admin"
  "roles/iam.serviceAccountUser"
  "roles/artifactregistry.writer"
  "roles/storage.admin"
  "roles/pubsub.admin"
)

for ROLE in "${ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$ROLE" \
    --condition=None --quiet > /dev/null
done

echo "================================================================="
echo " GCP Project Bootstrap complete!"
echo " Next: Run 'make deploy' or ./scripts/deploy.sh to deploy services."
echo "================================================================="

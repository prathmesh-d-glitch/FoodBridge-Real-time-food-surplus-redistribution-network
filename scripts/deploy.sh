#!/usr/bin/env bash
# ==============================================================================
# FoodBridge: End-to-End Cloud Deployment Script
# Builds containers, deploys Terraform infrastructure, and pushes to Cloud Run.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

PROJECT_ID="${1:-${GCP_PROJECT_ID:-}}"
REGION="${2:-${GCP_REGION:-asia-south1}}"
IMAGE_TAG="${3:-latest}"

if [ -z "$PROJECT_ID" ]; then
  echo "ERROR: GCP_PROJECT_ID is not set."
  echo "Usage: ./scripts/deploy.sh <PROJECT_ID> [REGION] [IMAGE_TAG]"
  exit 1
fi

REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/foodbridge"

echo "================================================================="
echo " Deploying FoodBridge Cloud Platform"
echo " Project: $PROJECT_ID | Region: $REGION | Tag: $IMAGE_TAG"
echo "================================================================="

# 1. Apply Terraform Infrastructure
echo "--> 1. Applying Terraform Cloud Infrastructure..."
cd "${ROOT_DIR}/infra/terraform"
terraform init
terraform apply -auto-approve \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="container_image_tag=${IMAGE_TAG}"

# 2. Build & Push Microservice Containers
SERVICES=("listing-service" "matching-service" "notification-service" "logistics-service" "analytics-service" "expiry-job")

cd "${ROOT_DIR}"
for SERVICE in "${SERVICES[@]}"; do
  IMAGE_NAME="${REGISTRY}/${SERVICE}:${IMAGE_TAG}"
  echo "--> Building container for: ${SERVICE}..."
  docker build -t "${IMAGE_NAME}" -f "services/${SERVICE}/Dockerfile" .

  echo "--> Pushing container to Artifact Registry: ${IMAGE_NAME}..."
  docker push "${IMAGE_NAME}"

  echo "--> Deploying ${SERVICE} to Cloud Run..."
  gcloud run deploy "foodbridge-${SERVICE}" \
    --image "${IMAGE_NAME}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --quiet
done

# 3. Build & Deploy Frontend PWA
echo "--> 3. Building Frontend Web PWA..."
cd "${ROOT_DIR}/web"
npm ci
npm run build

if command -v firebase &> /dev/null; then
  echo "--> Deploying Firebase security rules and hosting..."
  cd "${ROOT_DIR}/firebase"
  firebase deploy --project "${PROJECT_ID}" --only firestore:rules,storage:rules
fi

echo "================================================================="
echo " FoodBridge deployment complete!"
echo " Check Cloud Run console: https://console.cloud.google.com/run?project=${PROJECT_ID}"
echo "================================================================="

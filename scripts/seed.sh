#!/usr/bin/env bash
# ==============================================================================
# FoodBridge: Database Seeding Script
# Populates Firestore with verified Donors, NGOs, Listings, and Historical Impact
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "================================================================="
echo " Seeding FoodBridge Database (Donors, NGOs, Listings)"
echo "================================================================="

cd "${ROOT_DIR}"

if command -v python3 &> /dev/null; then
  PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
  PYTHON_CMD="python"
else
  echo "ERROR: Python is not installed."
  exit 1
fi

$PYTHON_CMD simulator/seed_data.py

echo "================================================================="
echo " Database seeding successfully completed!"
echo "================================================================="

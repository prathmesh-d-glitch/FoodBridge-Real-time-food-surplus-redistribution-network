# Dedicated least-privilege service accounts per microservice

resource "google_service_account" "sa_listing" {
  account_id   = "foodbridge-sa-listing"
  display_name = "FoodBridge Listing Service Account"
}

resource "google_service_account" "sa_matching" {
  account_id   = "foodbridge-sa-matching"
  display_name = "FoodBridge Matching Service Account"
}

resource "google_service_account" "sa_notification" {
  account_id   = "foodbridge-sa-notification"
  display_name = "FoodBridge Notification Service Account"
}

resource "google_service_account" "sa_logistics" {
  account_id   = "foodbridge-sa-logistics"
  display_name = "FoodBridge Logistics Service Account"
}

resource "google_service_account" "sa_analytics" {
  account_id   = "foodbridge-sa-analytics"
  display_name = "FoodBridge Analytics Service Account"
}

resource "google_service_account" "sa_expiry" {
  account_id   = "foodbridge-sa-expiry"
  display_name = "FoodBridge Expiry Job Service Account"
}

# Role bindings for Least-Privilege
resource "google_project_iam_member" "listing_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.sa_listing.email}"
}

resource "google_project_iam_member" "listing_pubsub_pub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.sa_listing.email}"
}

resource "google_project_iam_member" "matching_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.sa_matching.email}"
}

resource "google_project_iam_member" "matching_tasks_enqueuer" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.sa_matching.email}"
}

resource "google_project_iam_member" "matching_pubsub_pub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.sa_matching.email}"
}

resource "google_project_iam_member" "analytics_bq_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.sa_analytics.email}"
}

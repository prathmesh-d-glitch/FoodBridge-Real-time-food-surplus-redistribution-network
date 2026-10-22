output "listing_service_url" {
  description = "Public URL for Listing Service Cloud Run"
  value       = google_cloud_run_v2_service.listing_service.uri
}

output "matching_service_url" {
  description = "Public URL for Matching Service Cloud Run"
  value       = google_cloud_run_v2_service.matching_service.uri
}

output "analytics_service_url" {
  description = "Public URL for Analytics Service Cloud Run"
  value       = google_cloud_run_v2_service.analytics_service.uri
}

output "food_photos_bucket" {
  description = "GCS Bucket for Food Photos"
  value       = google_storage_bucket.food_photos.name
}

output "bigquery_dataset_id" {
  description = "BigQuery Platform Analytics Dataset"
  value       = google_bigquery_dataset.analytics.dataset_id
}

output "pubsub_dead_letter_topic" {
  description = "Dead Letter Topic for failed events"
  value       = google_pubsub_topic.dead_letter.id
}

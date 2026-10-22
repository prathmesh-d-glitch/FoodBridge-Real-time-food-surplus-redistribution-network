# BigQuery Analytics & Historical Forecasting Tables

resource "google_bigquery_dataset" "analytics" {
  dataset_id                  = "foodbridge_analytics"
  friendly_name               = "FoodBridge Platform Analytics"
  description                 = "Aggregated surplus redistribution impact and historical forecasts"
  location                    = var.region
  default_table_expiration_ms = null
}

resource "google_bigquery_table" "impact_records" {
  dataset_id          = google_bigquery_dataset.analytics.dataset_id
  table_id            = "impact_records"
  deletion_protection = false

  schema = jsonencode([
    { name = "id", type = "STRING", mode = "REQUIRED" },
    { name = "listing_id", type = "STRING", mode = "REQUIRED" },
    { name = "donor_id", type = "STRING", mode = "REQUIRED" },
    { name = "ngo_id", type = "STRING", mode = "REQUIRED" },
    { name = "quantity_kg", type = "FLOAT", mode = "REQUIRED" },
    { name = "meals_saved", type = "INTEGER", mode = "REQUIRED" },
    { name = "co2e_avoided_kg", type = "FLOAT", mode = "REQUIRED" },
    { name = "timestamp", type = "TIMESTAMP", mode = "REQUIRED" }
  ])
}

resource "google_bigquery_table" "listing_events" {
  dataset_id          = google_bigquery_dataset.analytics.dataset_id
  table_id            = "listing_events"
  deletion_protection = false

  schema = jsonencode([
    { name = "event_id", type = "STRING", mode = "REQUIRED" },
    { name = "event_type", type = "STRING", mode = "REQUIRED" },
    { name = "correlation_id", type = "STRING", mode = "NULLABLE" },
    { name = "timestamp", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "payload", type = "STRING", mode = "NULLABLE" }
  ])
}

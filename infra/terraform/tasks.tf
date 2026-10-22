# Cloud Tasks Queue for delayed cascading offer escalation

resource "google_cloud_tasks_queue" "offer_escalations" {
  name     = "cascading-offer-timeouts"
  location = var.region

  rate_limits {
    max_dispatches_per_second = 50
    max_concurrent_dispatches = 100
  }

  retry_config {
    max_attempts  = 5
    min_backoff   = "5s"
    max_backoff   = "60s"
    max_doublings = 3
  }
}

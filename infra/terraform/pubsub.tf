# Cloud Pub/Sub Event Topics and Push Subscriptions

locals {
  topics = [
    "listing-created",
    "match-offered",
    "offer-accepted",
    "offer-declined",
    "pickup-completed",
    "listing-expired",
    "admin-escalation",
  ]
}

resource "google_pubsub_topic" "event_topics" {
  for_each = toset(local.topics)
  name     = "foodbridge-${each.key}"
}

# Dead Letter Topic for unhandled failures
resource "google_pubsub_topic" "dead_letter" {
  name = "foodbridge-dead-letter"
}

# Push Subscription: listing.created -> matching-service
resource "google_pubsub_subscription" "sub_listing_created" {
  name  = "sub-matching-listing-created"
  topic = google_pubsub_topic.event_topics["listing-created"].id

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.matching_service.uri}/events/listing-created"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }

  ack_deadline_seconds = 60
}

# Push Subscription: pickup.completed -> analytics-service
resource "google_pubsub_subscription" "sub_pickup_completed" {
  name  = "sub-analytics-pickup-completed"
  topic = google_pubsub_topic.event_topics["pickup-completed"].id

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.analytics_service.uri}/events/pickup-completed"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }

  ack_deadline_seconds = 30
}

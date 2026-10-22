# Cloud Monitoring Dashboards & Alert Policies

resource "google_monitoring_notification_channel" "email" {
  display_name = "FoodBridge DevOps Alert Email"
  type         = "email"
  labels = {
    email_address = var.alert_notification_email
  }
}

# Alert on high Cloud Run 5xx errors
resource "google_monitoring_alert_policy" "cloud_run_5xx_errors" {
  display_name = "FoodBridge Microservices 5xx Error Spike"
  combiner     = "OR"
  conditions {
    display_name = "Cloud Run 5xx error rate > 5%"
    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\" AND metric.labels.response_code_class=\"5xx\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
}

# Alert on Dead Letter Queue backlog
resource "google_monitoring_alert_policy" "pubsub_dead_letter_spike" {
  display_name = "FoodBridge Pub/Sub Dead Letter Backlog"
  combiner     = "OR"
  conditions {
    display_name = "Dead letter topic receiving undeliverable messages"
    condition_threshold {
      filter          = "metric.type=\"pubsub.googleapis.com/topic/send_request_count\" AND resource.type=\"pubsub_topic\" AND resource.labels.topic_id=\"foodbridge-dead-letter\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_DELTA"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
}

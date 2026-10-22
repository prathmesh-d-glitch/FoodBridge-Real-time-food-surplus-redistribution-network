# Cloud Run v2 Services Deployment

resource "google_cloud_run_v2_service" "listing_service" {
  name     = "listing-service"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.sa_listing.email
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
    containers {
      image = "gcr.io/${var.project_id}/listing-service:${var.container_image_tag}"
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "EVENT_BUS_TYPE"
        value = "pubsub"
      }
      env {
        name  = "GEMINI_API_KEY"
        value = var.gemini_api_key
      }
    }
  }
}

resource "google_cloud_run_v2_service" "matching_service" {
  name     = "matching-service"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.sa_matching.email
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
    containers {
      image = "gcr.io/${var.project_id}/matching-service:${var.container_image_tag}"
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "EVENT_BUS_TYPE"
        value = "pubsub"
      }
    }
  }
}

resource "google_cloud_run_v2_service" "notification_service" {
  name     = "notification-service"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.sa_notification.email
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
    containers {
      image = "gcr.io/${var.project_id}/notification-service:${var.container_image_tag}"
      resources {
        limits = {
          cpu    = "1"
          memory = "256Mi"
        }
      }
      env {
        name  = "FCM_SERVER_KEY"
        value = var.fcm_server_key
      }
    }
  }
}

resource "google_cloud_run_v2_service" "logistics_service" {
  name     = "logistics-service"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.sa_logistics.email
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
    containers {
      image = "gcr.io/${var.project_id}/logistics-service:${var.container_image_tag}"
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
  }
}

resource "google_cloud_run_v2_service" "analytics_service" {
  name     = "analytics-service"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.sa_analytics.email
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
    containers {
      image = "gcr.io/${var.project_id}/analytics-service:${var.container_image_tag}"
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
  }
}

resource "google_cloud_run_v2_service" "expiry_job" {
  name     = "expiry-job"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    service_account = google_service_account.sa_expiry.email
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
    containers {
      image = "gcr.io/${var.project_id}/expiry-job:${var.container_image_tag}"
    }
  }
}

# Allow public invocations for frontend endpoints
resource "google_cloud_run_v2_service_iam_member" "public_listing" {
  name     = google_cloud_run_v2_service.listing_service.name
  location = google_cloud_run_v2_service.listing_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "public_matching" {
  name     = google_cloud_run_v2_service.matching_service.name
  location = google_cloud_run_v2_service.matching_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "public_analytics" {
  name     = google_cloud_run_v2_service.analytics_service.name
  location = google_cloud_run_v2_service.analytics_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

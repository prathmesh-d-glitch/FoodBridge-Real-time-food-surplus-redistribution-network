# Cloud Storage for food photos & generated CSR certificates

resource "google_storage_bucket" "food_photos" {
  name                        = "${var.project_id}-food-photos"
  location                    = var.region
  uniform_bucket_level_access = true

  cors {
    origin          = ["*"]
    method          = ["GET", "POST", "PUT", "HEAD"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  lifecycle_rule {
    condition {
      age = 30 # Delete surplus photos after 30 days
    }
    action {
      type = "Delete"
    }
  }
}

# Cloud Scheduler Job: Runs expiry scanner every 5 minutes

resource "google_cloud_scheduler_job" "expiry_job_trigger" {
  name             = "foodbridge-expiry-scanner"
  description      = "Scans active food surplus listings for expiration and triggers cascade escalation"
  schedule         = "*/5 * * * *"
  time_zone        = "Asia/Kolkata"
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.expiry_job.uri}/run"

    oidc_token {
      service_account_email = google_service_account.sa_expiry.email
    }
  }
}

variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
  default     = "foodbridge-prod"
}

variable "region" {
  description = "The GCP region to deploy resources into"
  type        = string
  default     = "asia-south1"
}

variable "environment" {
  description = "Deployment environment (e.g. dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "container_image_tag" {
  description = "Docker image tag for microservices deployment"
  type        = string
  default     = "latest"
}

variable "gemini_api_key" {
  description = "Google Gemini API key for AI photo analysis"
  type        = string
  default     = ""
  sensitive   = true
}

variable "fcm_server_key" {
  description = "Firebase Cloud Messaging server key for push dispatches"
  type        = string
  default     = ""
  sensitive   = true
}

variable "alert_notification_email" {
  description = "Email address for Cloud Monitoring escalation alerts"
  type        = string
  default     = "admin@foodbridge.org"
}

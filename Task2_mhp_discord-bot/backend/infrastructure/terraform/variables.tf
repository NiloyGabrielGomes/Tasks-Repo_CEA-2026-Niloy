variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-south-1"
}

variable "name_prefix" {
  description = "Prefix applied to all named resources (Lambda functions, roles, API, layer)"
  type        = string
  default     = "trainee-2026-niloy-mhp"
}

# ── Discord ──────────────────────────────────────────────────────────────────
variable "discord_public_key" {
  description = "Discord application public key for signature verification"
  type        = string
  sensitive   = true
}

variable "discord_application_id" {
  description = "Discord application ID"
  type        = string
}

variable "discord_bot_token" {
  description = "Discord bot token"
  type        = string
  sensitive   = true
}

variable "discord_guild_id" {
  description = "Discord server/guild ID"
  type        = string
}

variable "role_admin_id" {
  description = "Discord role ID for MHP-Admin"
  type        = string
  default     = ""
}

variable "role_team_lead_id" {
  description = "Discord role ID for MHP-TeamLead"
  type        = string
  default     = ""
}

# ── AWS data stores ──────────────────────────────────────────────────────────
variable "dynamodb_table_name" {
  description = "Name of the existing DynamoDB table"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the existing S3 bucket"
  type        = string
}

# ── Google Chat ──────────────────────────────────────────────────────────────
variable "enable_google_chat" {
  description = "Feature flag to enable Google Chat integration"
  type        = string
  default     = "true"

  validation {
    condition     = contains(["true", "false"], var.enable_google_chat)
    error_message = "enable_google_chat must be \"true\" or \"false\"."
  }
}

variable "google_chat_audience" {
  description = "JWT audience for Google Chat verification — set to API Gateway /google-chat URL"
  type        = string
  default     = ""
}

variable "google_chat_service_account_json" {
  description = "Base64-encoded GCP service account JSON key. Stored in SSM Parameter Store."
  type        = string
  sensitive   = true
  default     = ""
}

# ── Lambda policy defaults (overridable at runtime via /policy set) ──────────
variable "cutoff_time" {
  description = "Default meal update cutoff time (Asia/Dhaka)"
  type        = string
  default     = "21:00"
}

variable "wfh_monthly_cap" {
  description = "Default monthly WFH day cap"
  type        = string
  default     = "5"
}

variable "forward_planning_days" {
  description = "Default forward-planning window in days"
  type        = string
  default     = "7"
}

variable "timezone" {
  description = "Default timezone"
  type        = string
  default     = "Asia/Dhaka"
}

variable "enable_multi_lambda" {
  description = "Route commands to feature Lambdas (true) or run in-process (false)"
  type        = string
  default     = "true"
}

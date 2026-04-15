locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name

  dynamodb_table_arn = "arn:aws:dynamodb:${local.region}:${local.account_id}:table/${var.dynamodb_table_name}"
  dynamodb_index_arn = "${local.dynamodb_table_arn}/index/*"
  s3_bucket_arn      = "arn:aws:s3:::${var.s3_bucket_name}"
  s3_objects_arn     = "${local.s3_bucket_arn}/*"

  function_names = {
    ingress     = "${var.name_prefix}-ingress"
    meal        = "${var.name_prefix}-meal"
    location    = "${var.name_prefix}-location"
    override    = "${var.name_prefix}-override"
    headcount   = "${var.name_prefix}-headcount"
    google_chat = "${var.name_prefix}-gchat-ingress"
  }

  # Shared environment variables (mirrors SAM Globals.Function.Environment.Variables)
  common_env = {
    DISCORD_PUBLIC_KEY      = var.discord_public_key
    DISCORD_APPLICATION_ID  = var.discord_application_id
    DISCORD_BOT_TOKEN       = var.discord_bot_token
    DISCORD_GUILD_ID        = var.discord_guild_id
    DYNAMODB_TABLE_NAME     = var.dynamodb_table_name
    S3_BUCKET               = var.s3_bucket_name
    CUTOFF_TIME             = var.cutoff_time
    WFH_MONTHLY_CAP         = var.wfh_monthly_cap
    FORWARD_PLANNING_DAYS   = var.forward_planning_days
    TIMEZONE                = var.timezone
    ENABLE_MULTI_LAMBDA     = var.enable_multi_lambda
    MEAL_FUNCTION_NAME      = local.function_names.meal
    LOCATION_FUNCTION_NAME  = local.function_names.location
    OVERRIDE_FUNCTION_NAME  = local.function_names.override
    HEADCOUNT_FUNCTION_NAME = local.function_names.headcount
    ENABLE_GOOGLE_CHAT      = var.enable_google_chat
    GOOGLE_CHAT_AUDIENCE    = var.google_chat_audience
  }

  ingress_extra_env = {
    ROLE_ADMIN_ID     = var.role_admin_id
    ROLE_TEAM_LEAD_ID = var.role_team_lead_id
  }

  # GOOGLE_CHAT_SERVICE_ACCOUNT_JSON omitted — lives in SSM Parameter Store (env var 4KB limit).
  google_chat_env = {
    DYNAMODB_TABLE_NAME   = var.dynamodb_table_name
    S3_BUCKET             = var.s3_bucket_name
    CUTOFF_TIME           = var.cutoff_time
    WFH_MONTHLY_CAP       = var.wfh_monthly_cap
    FORWARD_PLANNING_DAYS = var.forward_planning_days
    TIMEZONE              = var.timezone
    ENABLE_GOOGLE_CHAT    = var.enable_google_chat
    GOOGLE_CHAT_AUDIENCE  = var.google_chat_audience
    ROLE_ADMIN_ID         = var.role_admin_id
    ROLE_TEAM_LEAD_ID     = var.role_team_lead_id
  }

  backend_root   = "${path.module}/../.."        # Task2_mhp_discord-bot/backend
  build_root     = "${path.module}/.build"       # staged artifacts per function
  layer_build    = "${local.build_root}/layer"
}

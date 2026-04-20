locals {
  lambda_runtime      = "python3.12"
  lambda_timeout      = 30
  lambda_memory_size  = 256
}

# ── Ingress: signature verification, auth, dispatch ──────────────────────────
resource "aws_lambda_function" "ingress" {
  function_name    = local.function_names.ingress
  role             = aws_iam_role.ingress.arn
  handler          = "src.handlers.ingress.lambda_handler"
  runtime          = local.lambda_runtime
  timeout          = local.lambda_timeout
  memory_size      = local.lambda_memory_size
  filename         = data.archive_file.function_zip["ingress"].output_path
  source_code_hash = data.archive_file.function_zip["ingress"].output_base64sha256
  layers           = [aws_lambda_layer_version.shared_deps.arn]

  environment {
    variables = merge(local.common_env, local.ingress_extra_env)
  }
}

# ── Feature Lambdas (invoked synchronously by ingress) ───────────────────────
resource "aws_lambda_function" "meal" {
  function_name    = local.function_names.meal
  role             = aws_iam_role.feature.arn
  handler          = "src.handlers.meal_handler.lambda_handler"
  runtime          = local.lambda_runtime
  timeout          = local.lambda_timeout
  memory_size      = local.lambda_memory_size
  filename         = data.archive_file.function_zip["meal"].output_path
  source_code_hash = data.archive_file.function_zip["meal"].output_base64sha256
  layers           = [aws_lambda_layer_version.shared_deps.arn]

  environment {
    variables = local.common_env
  }
}

resource "aws_lambda_function" "location" {
  function_name    = local.function_names.location
  role             = aws_iam_role.feature.arn
  handler          = "src.handlers.location_handler.lambda_handler"
  runtime          = local.lambda_runtime
  timeout          = local.lambda_timeout
  memory_size      = local.lambda_memory_size
  filename         = data.archive_file.function_zip["location"].output_path
  source_code_hash = data.archive_file.function_zip["location"].output_base64sha256
  layers           = [aws_lambda_layer_version.shared_deps.arn]

  environment {
    variables = local.common_env
  }
}

resource "aws_lambda_function" "override" {
  function_name    = local.function_names.override
  role             = aws_iam_role.feature.arn
  handler          = "src.handlers.override_handler.lambda_handler"
  runtime          = local.lambda_runtime
  timeout          = local.lambda_timeout
  memory_size      = local.lambda_memory_size
  filename         = data.archive_file.function_zip["override"].output_path
  source_code_hash = data.archive_file.function_zip["override"].output_base64sha256
  layers           = [aws_lambda_layer_version.shared_deps.arn]

  environment {
    variables = local.common_env
  }
}

resource "aws_lambda_function" "headcount" {
  function_name    = local.function_names.headcount
  role             = aws_iam_role.feature.arn
  handler          = "src.handlers.headcount_handler.lambda_handler"
  runtime          = local.lambda_runtime
  timeout          = local.lambda_timeout
  memory_size      = local.lambda_memory_size
  filename         = data.archive_file.function_zip["headcount"].output_path
  source_code_hash = data.archive_file.function_zip["headcount"].output_base64sha256
  layers           = [aws_lambda_layer_version.shared_deps.arn]

  environment {
    variables = local.common_env
  }
}

# ── Google Chat ingress ──────────────────────────────────────────────────────
# Uses its own env map (replaces Globals — mirrors SAM function-level Environment behavior).
resource "aws_lambda_function" "google_chat" {
  function_name    = local.function_names.google_chat
  role             = aws_iam_role.google_chat.arn
  handler          = "src.handlers.google_chat_ingress.lambda_handler"
  runtime          = local.lambda_runtime
  timeout          = local.lambda_timeout
  memory_size      = local.lambda_memory_size
  filename         = data.archive_file.function_zip["google_chat"].output_path
  source_code_hash = data.archive_file.function_zip["google_chat"].output_base64sha256
  layers           = [aws_lambda_layer_version.shared_deps.arn]

  environment {
    variables = local.google_chat_env
  }
}

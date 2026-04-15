data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# ── Ingress role: logs + Lambda invoke + limited DynamoDB (upsert_user) ─────
resource "aws_iam_role" "ingress" {
  name               = "${var.name_prefix}-ingress-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ingress_basic_exec" {
  role       = aws_iam_role.ingress.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "ingress_invoke" {
  statement {
    effect  = "Allow"
    actions = ["lambda:InvokeFunction"]
    resources = [
      aws_lambda_function.meal.arn,
      aws_lambda_function.location.arn,
      aws_lambda_function.override.arn,
      aws_lambda_function.headcount.arn,
    ]
  }
}

resource "aws_iam_role_policy" "ingress_invoke" {
  name   = "${var.name_prefix}-ingress-invoke-policy"
  role   = aws_iam_role.ingress.id
  policy = data.aws_iam_policy_document.ingress_invoke.json
}

data "aws_iam_policy_document" "ingress_dynamodb" {
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [local.dynamodb_table_arn]
  }
}

resource "aws_iam_role_policy" "ingress_dynamodb" {
  name   = "${var.name_prefix}-ingress-dynamodb-policy"
  role   = aws_iam_role.ingress.id
  policy = data.aws_iam_policy_document.ingress_dynamodb.json
}

# ── Feature role: DynamoDB + S3 ─────────────────────────────────────────────
resource "aws_iam_role" "feature" {
  name               = "${var.name_prefix}-feature-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "feature_basic_exec" {
  role       = aws_iam_role.feature.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "feature_dynamodb" {
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:BatchWriteItem",
    ]
    resources = [
      local.dynamodb_table_arn,
      local.dynamodb_index_arn,
    ]
  }
}

resource "aws_iam_role_policy" "feature_dynamodb" {
  name   = "${var.name_prefix}-feature-dynamodb-policy"
  role   = aws_iam_role.feature.id
  policy = data.aws_iam_policy_document.feature_dynamodb.json
}

data "aws_iam_policy_document" "feature_s3" {
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      local.s3_bucket_arn,
      local.s3_objects_arn,
    ]
  }
}

resource "aws_iam_role_policy" "feature_s3" {
  name   = "${var.name_prefix}-feature-s3-policy"
  role   = aws_iam_role.feature.id
  policy = data.aws_iam_policy_document.feature_s3.json
}

# ── Google Chat ingress role: DynamoDB + S3 + SSM ───────────────────────────
resource "aws_iam_role" "google_chat" {
  name               = "${var.name_prefix}-gchat-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "gchat_basic_exec" {
  role       = aws_iam_role.google_chat.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "gchat_dynamodb" {
  name   = "${var.name_prefix}-gchat-dynamodb-policy"
  role   = aws_iam_role.google_chat.id
  policy = data.aws_iam_policy_document.feature_dynamodb.json
}

resource "aws_iam_role_policy" "gchat_s3" {
  name   = "${var.name_prefix}-gchat-s3-policy"
  role   = aws_iam_role.google_chat.id
  policy = data.aws_iam_policy_document.feature_s3.json
}

data "aws_iam_policy_document" "gchat_ssm" {
  statement {
    effect  = "Allow"
    actions = ["ssm:GetParameter"]
    resources = [
      "arn:aws:ssm:${local.region}:${local.account_id}:parameter/mhp/gchat-sa-json",
    ]
  }
}

resource "aws_iam_role_policy" "gchat_ssm" {
  name   = "${var.name_prefix}-gchat-ssm-policy"
  role   = aws_iam_role.google_chat.id
  policy = data.aws_iam_policy_document.gchat_ssm.json
}

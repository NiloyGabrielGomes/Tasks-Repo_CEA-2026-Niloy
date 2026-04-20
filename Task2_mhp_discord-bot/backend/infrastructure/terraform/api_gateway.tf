resource "aws_apigatewayv2_api" "bot" {
  name          = "${var.name_prefix}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.bot.id
  name        = "prod"
  auto_deploy = true
}

# ── /discord → InteractionFunction ───────────────────────────────────────────
resource "aws_apigatewayv2_integration" "discord" {
  api_id                 = aws_apigatewayv2_api.bot.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.ingress.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "discord" {
  api_id    = aws_apigatewayv2_api.bot.id
  route_key = "POST /discord"
  target    = "integrations/${aws_apigatewayv2_integration.discord.id}"
}

resource "aws_lambda_permission" "discord" {
  statement_id  = "AllowExecutionFromAPIGatewayDiscord"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingress.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.bot.execution_arn}/*/*/discord"
}

# ── /google-chat → GoogleChatFunction ────────────────────────────────────────
resource "aws_apigatewayv2_integration" "google_chat" {
  api_id                 = aws_apigatewayv2_api.bot.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.google_chat.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "google_chat" {
  api_id    = aws_apigatewayv2_api.bot.id
  route_key = "POST /google-chat"
  target    = "integrations/${aws_apigatewayv2_integration.google_chat.id}"
}

resource "aws_lambda_permission" "google_chat" {
  statement_id  = "AllowExecutionFromAPIGatewayGoogleChat"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.google_chat.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.bot.execution_arn}/*/*/google-chat"
}

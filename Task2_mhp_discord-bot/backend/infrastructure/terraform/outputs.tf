output "bot_api_endpoint" {
  description = "Base API URL — Discord uses /discord, Google Chat uses /google-chat"
  value       = "${aws_apigatewayv2_api.bot.api_endpoint}/${aws_apigatewayv2_stage.prod.name}"
}

output "interaction_function_arn" {
  description = "Discord ingress Lambda ARN"
  value       = aws_lambda_function.ingress.arn
}

output "google_chat_function_arn" {
  description = "Google Chat ingress Lambda ARN"
  value       = aws_lambda_function.google_chat.arn
}

output "headcount_function_arn" {
  description = "Headcount summary Lambda ARN"
  value       = aws_lambda_function.headcount.arn
}

output "shared_deps_layer_arn" {
  description = "Shared Lambda layer ARN"
  value       = aws_lambda_layer_version.shared_deps.arn
}

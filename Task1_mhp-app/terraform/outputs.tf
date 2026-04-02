output "public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.mhp_app_server.public_ip
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/trainee-2026-niloy-key.pem ec2-user@${aws_instance.mhp_app_server.public_ip}"
}

output "swagger_url" {
  description = "Swagger UI URL"
  value       = "http://${aws_instance.mhp_app_server.public_ip}:8000/docs"
}

output "health_url" {
  description = "Health check URL"
  value       = "http://${aws_instance.mhp_app_server.public_ip}:8000/health"
}

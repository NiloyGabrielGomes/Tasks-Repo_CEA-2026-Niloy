variable "repo_url" {
  description = "Public GitHub repository URL to clone"
  type        = string
  default     = "https://github.com/NiloyGabrielGomes/Tasks-Repo_CEA-2026-Niloy.git"
}

variable "branch_name" {
  description = "Git branch to clone"
  type        = string
  default     = "deploy/task1_ec2"
}

variable "key_pair_name" {
  description = "Name of an existing AWS key pair for SSH access"
  type        = string
  default     = "trainee-2026-niloy-key"
}

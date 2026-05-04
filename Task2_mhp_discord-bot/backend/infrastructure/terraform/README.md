# Terraform Infrastructure — MHP Backend

Parallel Terraform stack to the existing SAM deployment (`../template.yaml`). Both are kept in the repo; Terraform is the primary path for Jenkins CI/CD, SAM remains as a fallback.

## Layout

| File | Purpose |
|---|---|
| `main.tf` | Provider, backend, data sources |
| `variables.tf` | Input variables (mirrors SAM `Parameters`) |
| `locals.tf` | Shared env vars, ARN composition, function names |
| `iam.tf` | Three execution roles: ingress, feature, google_chat |
| `lambda_layer.tf` | Shared deps layer |
| `build.tf` | `null_resource` wrappers around `Makefile` + layer pip install |
| `lambda_functions.tf` | All 6 Lambda functions |
| `api_gateway.tf` | HTTP API v2, routes, integrations, permissions |
| `outputs.tf` | Stack outputs (mirrors SAM `Outputs`) |
| `terraform.tfvars.example` | Template for local values — copy to `terraform.tfvars` |

## Prerequisites

- Terraform ≥ 1.5
- AWS credentials with permissions to create Lambda, IAM, API Gateway v2 resources
- `make` and `bash` on PATH (Windows: Git Bash + `choco install make`)
- Python 3.12 + `pip` (for building the layer)
- Existing DynamoDB table and S3 bucket matching `dynamodb_table_name` and `s3_bucket_name`

## Usage

```bash
cd Task2_mhp_discord-bot/backend/infrastructure/terraform

cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars with real values

terraform init
terraform plan -out=plan.tfplan
terraform apply plan.tfplan
```

## Build Orchestration

Terraform doesn't build code natively. `build.tf` invokes the existing `Makefile` targets via `null_resource` + `local-exec`:

- **Layer**: `pip install -r layer/requirements.txt -t .build/layer/python` then zip
- **Per-function**: `ARTIFACTS_DIR=.build/<name> make build-<Target>` then zip

Changes to `src/**/*.py` invalidate `local.src_hash`, which re-runs all function builds. Changes to `layer/requirements.txt` re-run the layer build.

## Remote State

The S3 backend block in `main.tf` is commented out. For team/CI use:

1. Pre-create an S3 bucket and a DynamoDB lock table (outside Terraform or via a bootstrap stack)
2. Uncomment the `backend "s3"` block
3. Run `terraform init -migrate-state`

## Jenkins

The Jenkinsfile (separate task) will run:

```
terraform init \
  && terraform plan -out=plan.tfplan \
  && (archive plan.tfplan for approval) \
  && terraform apply plan.tfplan
```

Secrets (`discord_bot_token`, `discord_public_key`, `google_chat_service_account_json`) should come from Jenkins credentials bindings as `TF_VAR_*` environment variables, not from `terraform.tfvars`.

## Side-by-Side with SAM

Both stacks use the same DynamoDB table and S3 bucket (they're parameters, not managed resources). To run both simultaneously without collision, override `name_prefix` for the Terraform stack:

```hcl
name_prefix = "trainee-2026-niloy-mhp-tf"
```

This gives the Terraform-managed Lambdas, roles, and API distinct names. Revert to `trainee-2026-niloy-mhp` once SAM is retired.

## Known Gaps vs SAM

- `GoogleChatServiceAccountJson` parameter accepted but not wired to SSM — upload separately via AWS CLI:
  ```
  aws ssm put-parameter --name /mhp/gchat-sa-json --type SecureString --value "$JSON"
  ```
- CloudFormation stack exports (`!Sub ${AWS::StackName}-...`) have no Terraform equivalent. Use remote state data sources or Terraform outputs if other stacks need these ARNs.

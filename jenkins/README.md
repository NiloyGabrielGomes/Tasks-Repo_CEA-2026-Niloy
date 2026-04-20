# Jenkins Setup

Docker-based Jenkins for running the Terraform pipeline defined in the repo-root `Jenkinsfile`. This enables repeatable, audited, and approval-gated Terraform plan/apply workflows for Task2 backend infrastructure.

## Architecture

```
Local Machine (Windows)
    ↓
Docker Desktop
    ↓
Jenkins Container (custom image: JDK17 + Terraform + AWS CLI + Make + Python)
    ↓
jenkins_home/ (local volume mount for persistence)
    ↓
Git clone of this repo (from GitHub)
    ↓
Jenkinsfile → terraform init/validate/plan → (manual approval) → terraform apply
    ↓
AWS (DynamoDB, Lambda, API Gateway, S3, etc.)
```

## File Layout

| File | Role |
|---|---|
| `Dockerfile` | Custom Jenkins image (JDK17) + Terraform 1.9.8 + AWS CLI v2 + Make + Python 3 pre-installed |
| `docker-compose.yml` | Defines Jenkins container, port 8080, and local volume mount for jenkins_home |
| `Jenkinsfile` (repo root) | Pipeline definition: checkout, terraform plan with approval gate, terraform apply |

## Setup (Docker Desktop on Windows)

### 1. Start Jenkins container

Run from this directory (`jenkins/`):

```bash
cd jenkins
docker compose up -d
```

This:
- Builds the custom Jenkins image (if not cached) from `Dockerfile`.
- Starts the Jenkins container named `jenkins-mhp`.
- Mounts `./jenkins_home` as a local volume so data persists across restarts.
- Exposes port 8080 locally.

### 2. Retrieve initial admin password

```bash
docker exec jenkins-mhp cat /var/jenkins_home/secrets/initialAdminPassword
```

This outputs a one-time password required for first-time Jenkins setup.

### 3. Open Jenkins UI and initialize

1. Open `http://localhost:8080` in a browser.
2. Paste the password from step 2.
3. Click "Install suggested plugins" (or customize if needed).
4. Wait for plugins to install (~2-5 minutes depending on internet speed).
5. Create your admin user account (username, password, email).
6. Skip "Configure Jenkins Instance" defaults and click "Save and Continue".
7. You should see the Jenkins dashboard.

### 4. Add credentials to Jenkins

Jenkins needs credentials for AWS and Discord configuration to pass to Terraform. These are not stored in `terraform.tfvars` (which stays in the repo).

**Navigation**: `Manage Jenkins` → `Credentials` → `System` → `Global credentials` → `Add credentials`

Create the following credentials (Kind, ID):

| Kind | ID | Value Source |
|---|---|---|
| Username with password | `aws-mhp-deploy` | Your AWS Access Key ID (username) and Secret Key (password) |
| Secret text | `discord-public-key` | From Discord Developer Portal (your bot's public key) |
| Secret text | `discord-bot-token` | From Discord Developer Portal (your bot's token) |
| Secret text | `discord-application-id` | From Discord Developer Portal (your bot's application/client ID) |
| Secret text | `discord-guild-id` | Your Discord server ID (where the bot is installed) |
| Secret text | `role-admin-id` | Discord role ID for admin users in your server |
| Secret text | `role-team-lead-id` | Discord role ID for team lead users in your server |

### 5. Create the pipeline job

**Navigation**: Dashboard → `New Item`

Configure:
- **Name**: `mhp-backend-deploy`
- **Type**: `Pipeline`
- Click `OK`

In the pipeline configuration:
- **Definition**: `Pipeline script from SCM`
- **SCM**: `Git`
  - **Repository URL**: `https://github.com/NiloyGabrielGomes/Tasks-Repo_CEA-2026-Niloy` (or your fork)
  - **Branch**: `*/infra/issue23/Terraform_Jenkins_Migration` (change to `*/main` after PR merge)
- **Script Path**: `Jenkinsfile` 
- Click `Save`

## Running the Pipeline

### Trigger a build

1. Go to the `mhp-backend-deploy` job page.
2. Click `Build Now`.
3. Jenkins will:
   - Clone the repo from the branch you configured.
   - Run the `Jenkinsfile` pipeline.
   - Execute Terraform stages in order.

### Pipeline stages (from `Jenkinsfile`)

1. **Checkout**: Git clone from the configured branch.
2. **Plan**:
   - `cd Task2_mhp_discord-bot/backend/infrastructure/terraform`
   - `terraform init` (initializes backend and plugins)
   - `terraform validate` (syntax/schema check)
   - `terraform plan -out=tfplan` (preview changes)
   - Credentials injected as `TF_VAR_*` environment variables.
3. **Approve** (manual gate):
4. **Apply**:
   - `terraform apply -input=false tfplan` (executes the saved plan).
   - Infrastructure created/updated in AWS.
   - Results logged to CloudWatch (via Jenkins logs).

### Monitoring the build

In Jenkins:
- Click the build number to see full logs.
- Scroll through to check for errors or unexpected resource changes.
- If the plan looks wrong, abort the build before the approval stage.

## Local Runtime State

The `jenkins_home/` directory:
- Created automatically on first `docker compose up -d`.
- **Gitignored** (see root `.gitignore`) because it contains runtime state and secrets.

To reset Jenkins to a clean state:
```bash
rm -rf jenkins_home
docker compose down
docker compose up -d
# Repeat setup steps above
```

## Stopping and Restarting Jenkins

Stop the container:
```bash
docker compose down
```

Restart (with all configuration/credentials preserved):
```bash
docker compose up -d
```

View logs:
```bash
docker compose logs -f jenkins
```

## Custom Docker Image Details

The `Dockerfile` builds a Jenkins image with:
- **Base**: `jenkins/jenkins:lts-jdk17` (Long-Term Support + JDK 17)
- **System tools**: `curl`, `unzip`, `make`, `python3`, `python3-pip`, `ca-certificates`
- **AWS CLI v2**: Downloaded and installed from official AWS zip.
- **Terraform**: Version 1.9.8 downloaded and installed to `/usr/local/bin`.


## Troubleshooting

**Jenkins won't start**: Check Docker Desktop is running and port 8080 is not in use.
```bash
docker ps  # Lists running containers
docker logs jenkins-mhp  # Shows Jenkins startup logs
```

**Terraform plan fails with "access denied"**: AWS credentials in Jenkins are wrong or missing. Re-verify in `Manage Jenkins → Credentials`.

**Pipeline job not found**: Check the `Script Path` is `Jenkinsfile` (at repo root, not in a subdirectory).

**Plan looks wrong**: Abort before the approval stage. Adjust `terraform.tfvars` or Terraform code and push a new commit, then trigger a new build.

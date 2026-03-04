# MHP Discord Bot — Technical Documentation

> **Version:** 1.2.0  
> **Last Updated:** 2026-03-04  
> **Status:** Issue #3 Complete — Meal Participation for Employees
> **Addressed Issues:** #1, #2, #3

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Infrastructure](#infrastructure)
4. [DynamoDB Schema](#dynamodb-schema)
5. [Discord Integration](#discord-integration)
6. [Authentication & Authorization](#authentication--authorization)
7. [Meal Participation](#meal-participation)
8. [Security](#security)
9. [Future Enhancements](#future-enhancements)

---

## Overview

This document covers the technical implementation of the Meal Headcount Planner (MHP) Discord Bot. The bot provides employees a way to manage their meal participation and work locations via Discord slash commands, with admin/team lead reporting capabilities.

### Goals

- Employees can update meal participation and work location via Discord
- Team Leads can view team-level summaries
- Admins can view overall headcount and trigger reports
- Fully serverless architecture (no persistent servers)

---

## Architecture

### Tech Stack

| Component | Technology |
|-----------|------------|
| Runtime | Python 3.12.x |
| Compute | AWS Lambda |
| API Gateway | AWS API Gateway |
| Database | Amazon DynamoDB |
| Storage | Amazon S3 |
| Discord Integration | Discord HTTP Interactions (PyNaCl) |
| Infrastructure | AWS SAM |

### High-Level Flow

```
User → Discord → API Gateway → Lambda → DynamoDB/S3
                ↓
         PyNaCl Signature
         Verification
         ↓
    Role-based Access
    Control (RBAC)
```

---

## Infrastructure

### AWS Resources

All infrastructure is defined in [`infrastructure/template.yaml`](infrastructure/template.yaml) using AWS SAM.

#### Lambda Function

- **Function Name:** `mhp-interaction-{environment}`
- **Runtime:** Python 3.12
- **Timeout:** 30 seconds
- **Memory:** 256 MB
- **Handler:** `src.handlers.interaction.lambda_handler`

#### API Gateway

- **Path:** `/interactions`
- **Method:** POST
- **Integration:** Lambda Proxy

#### DynamoDB Table

- **Name:** `mhp-{environment}-data`
- **Billing:** Pay-per-request (on-demand)
- **Keys:** PK (Partition Key), SK (Sort Key)
- **GSIs:** None required

#### S3 Bucket

- **Name:** `mhp-{environment}-reports`
- **Purpose:** Storage for generated reports and temporary data
- **Encryption:** AES-256

### Environment Variables

#### Required Secrets (store in AWS Secrets Manager)

| Variable | Description |
|----------|-------------|
| `DISCORD_PUBLIC_KEY` | Discord app public key (hex format) |
| `DISCORD_BOT_TOKEN` | Discord bot token |
| `DISCORD_CLIENT_SECRET` | Discord OAuth2 client secret |
| `SECRET_KEY` | Internal JWT signing key |

#### Required Config

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_APPLICATION_ID` | Discord application ID | (required) |
| `DISCORD_CLIENT_ID` | Discord OAuth2 client ID | (required) |
| `DISCORD_GUILD_ID` | Discord server ID | (required) |
| `DISCORD_REDIRECT_URI` | OAuth2 callback URI | (required) |
| `ROLE_ADMIN_ID` | Discord role ID for admins | (optional) |
| `ROLE_TEAM_LEAD_ID` | Discord role ID for team leads | (optional) |

#### Application Config

| Variable | Description | Default |
|----------|-------------|---------|
| `DYNAMODB_TABLE_NAME` | DynamoDB table name | `mhp-dev-data` |
| `S3_BUCKET` | S3 bucket name | `mhp-dev-reports` |
| `CUTOFF_TIME` | Meal update cutoff (Dhaka) | `21:00` |
| `WFH_MONTHLY_CAP` | WFH days per month | `5` |
| `FORWARD_PLANNING_DAYS` | Max days ahead to book | `7` |
| `TIMEZONE` | timezone | `Asia/Dhaka` |
| `DEBUG` | Enable debug mode | `false` |

#### Role Mapping Config

| Variable | Description | Default |
|----------|-------------|---------|
| `ROLE_ADMIN` | Discord role name for admins | `MHP-Admin` |
| `ROLE_TEAM_LEAD` | Discord role name for team leads | `MHP-TeamLead` |
| `ROLE_EMPLOYEE` | Default role for employees | `MHP-Employee` |

---

## DynamoDB Schema

### Design Principles

- **Single-table design** — All entities in one DynamoDB table
- **No GSIs** — All access patterns use primary key queries
- **Partition by date** — Most common queries are date-based
- **Team stamped at write time** — Team name (from the user's Discord team role) is written on every meal/location record. Team queries use `Query` on date PK + `FilterExpression` on `team`. Discord roles remain the source of truth; the stamp is refreshed on every update.

### Key Structure

| PK (Partition Key) | SK (Sort Key) | Entity Type |
|---|---|---|
| `USER#{discord_id}` | `PROFILE` | User profile |
| `DATE#{date}#MEAL` | `USER#{discord_id}#{meal_type}` | Meal participation |
| `DATE#{date}#LOCATION` | `USER#{discord_id}` | Work location |
| `SPECIALDAY#{date}` | `-` | Special day config |
| `POLICY#{name}` | `-` | Policy settings |

### Access Patterns

| Operation | Query | Key Expression |
|-----------|-------|----------------|
| Get all meals for date | Query | `PK = DATE#2026-02-26#MEAL` |
| Get user's meal for date | Query | `PK = DATE#2026-02-26#MEAL`, SK begins with `USER#123` |
| Get team meals for date | Query + Filter | `PK = DATE#2026-02-26#MEAL`, Filter `team = "Team-Backend"` |
| Get all locations for date | Query | `PK = DATE#2026-02-26#LOCATION` |
| Get team locations for date | Query + Filter | `PK = DATE#2026-02-26#LOCATION`, Filter `team = "Team-Backend"` |
| Get user profile | Get | `PK = USER#123`, `SK = PROFILE` |
| Get special day | Get | `PK = SPECIALDAY#2026-02-26` |
| Get policy | Get | `PK = POLICY#cutoff_time` |

### Data Models

#### User

```python
class User:
    discord_id: str      # Primary identifier
    name: str           # Display name
    email: str         # Email (optional)
    role: UserRole     # employee, team_lead, admin
    team: str          # Team name (optional)
    is_active: bool    # Account status
    created_at: datetime
```

#### MealParticipation

```python
class MealParticipation:
    user_id: str           # Discord user ID
    date: date            # Meal date
    meal_type: MealType   # lunch, snacks, iftar, etc.
    is_participating: bool # True = opted in, False = opted out
    team: str             # Team name stamped from Discord role at write time
    updated_by: str       # Who made the update
    updated_at: datetime
    reason: str          # Optional reason for change
```

#### WorkLocation

```python
class WorkLocation:
    user_id: str           # Discord user ID
    date: date            # Location date
    location: WorkLocationType  # office, wfh
    team: str             # Team name stamped from Discord role at write time
    updated_by: str       # Who made the update
    updated_at: datetime
```

#### SpecialDay

```python
class SpecialDay:
    date: date            # The date
    day_type: DayType    # office_closed, government_holiday, celebration
    note: str            # Optional note
```

#### Policy

```python
class Policy:
    name: str            # Policy name (e.g., "cutoff_time")
    value: str           # Policy value
    updated_at: datetime
```

---

## Discord Integration

### How It Works

1. **Slash Command** — User types `/meal-update` in Discord
2. **Discord to Lambda** — Discord sends HTTP POST to API Gateway endpoint
3. **Signature Verification** — PyNaCl verifies Ed25519 signature
4. **Authentication** — Extract user identity and roles from interaction payload
5. **Authorization** — Check if user has permission for the command
6. **Process & Respond** — Lambda processes request and returns response

### Signature Verification

The Lambda handler verifies every request using PyNaCl:

```python
from nacl.signing import VerifyKey
from nacl.encoding import RawEncoder

verify_key = VerifyKey(bytes.fromhex(public_key))
message = timestamp.encode() + event_body.encode()
verify_key.verify(message, bytes.fromhex(signature), encoder=RawEncoder)
```

### Response Types

| Type | Code | Use Case |
|------|------|----------|
| PONG | 1 | Ping/pong verification |
| CHANNEL_MESSAGE | 4 | Regular response |
| DEFERRED_CHANNEL_MESSAGE | 5 | Long processing |
| UPDATE_MESSAGE | 7 | Update original message |

---

## Authentication & Authorization

### Overview

The bot uses Discord as the identity provider. Every interaction includes user identity and server roles, eliminating the need for separate login flows.

### Authentication Flow

```
1. User interacts with bot (slash command / button)
         ↓
2. Discord sends interaction to Lambda
         ↓
3. PyNaCl verifies signature
         ↓
4. Extract user from interaction payload:
   - discord_id
   - username
   - global_name
   - guild_id
   - roles (list of role IDs)
         ↓
5. Map Discord roles to application role
         ↓
6. Create AuthenticatedUser object
```

### User Extraction

```python
@dataclass
class AuthenticatedUser:
    discord_id: str           # User's Discord ID
    username: str            # Discord username
    global_name: Optional[str]  # Display name
    role: UserRole          # Mapped application role
    team: Optional[str]      # Derived from Discord roles
    guild_id: str           # Server ID
    discord_roles: list[str]  # Raw Discord role IDs
```

### Role Mapping

Discord server roles are mapped to application roles:

| Discord Role | Application Role | Permission Level |
|--------------|------------------|------------------|
| MHP-Admin (role ID) | `admin` | 2 (highest) |
| MHP-TeamLead (role ID) | `team_lead` | 1 |
| (no special role) | `employee` | 0 (lowest) |

### Authorization Implementation

```python
# Command role requirements (defined in auth.py)
COMMAND_ROLE_REQUIREMENTS = {
    "meal-update": UserRole.EMPLOYEE,
    "work-location": UserRole.EMPLOYEE,
    "team-summary": UserRole.TEAM_LEAD,
    "headcount-summary": UserRole.ADMIN,
    "override-update": UserRole.ADMIN,
    "generate-summary": UserRole.ADMIN,
}

def check_command_authorization(command_name: str, user: AuthenticatedUser):
    required_role = COMMAND_ROLE_REQUIREMENTS.get(command_name)
    if user.role.level < required_role.level:
        return False, "❌ You don't have permission to use this command."
    return True, None
```

### Unauthorized Response

When a user tries to execute a command they don't have permission for:

```json
{
  "type": 4,
  "data": {
    "content": "❌ You don't have permission to use this command. Required role: admin",
    "flags": 64
  }
}
```

The `flags: 64` makes the message ephemeral (only the user sees it).

---

## Security

### Signature Verification

- All Discord requests verified with Ed25519 (PyNaCl)
- Invalid signatures return 401 Unauthorized

### Role-based Access Control

- Users can only execute commands permitted by their role
- Role mapping happens on every interaction (no cached roles)
- Unauthorized attempts are logged and return clear error messages

### AWS IAM

- Lambda execution role with minimal permissions
- DynamoDB: GetItem, PutItem, Query, Scan
- S3: PutObject, GetObject, ListBucket

### Discord Bot Permissions

Required scopes:
- `applications.commands` — Slash commands
- `bot` — Bot user

### Secrets Management

For production deployments, store sensitive values in AWS Secrets Manager:

```
Secrets Manager → Lambda Environment Variables → Application
```

Recommended secrets:
- `DISCORD_PUBLIC_KEY`
- `DISCORD_BOT_TOKEN`
- `DISCORD_CLIENT_SECRET`
- `SECRET_KEY`

---

## Future Enhancements

### Planned Features

- **EventBridge Integration** — Scheduled daily summary generation
- **Team-based Queries** — Team name stamped on records at write time; team queries use `Query` + `FilterExpression`. TL's team derived from interaction payload roles (zero extra API calls). GSI can be added later if filter cost becomes a concern at scale.
- **Web Dashboard** — Separate web interface for admins (Task 3)
- **Discord Announcements** — Auto-post summaries to channels
- **OAuth2 Flow** — For web dashboard authentication and discord and lambda request processing

---

*This documentation will be updated as new issues are implemented.*

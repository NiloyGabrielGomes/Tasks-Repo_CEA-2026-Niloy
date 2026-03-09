# MHP Discord Bot — Technical Documentation

> **Version:** 1.4.0  
> **Last Updated:** 2026-03-09  
> **Status:** Issue #5 Complete — Admin/Team Lead Override Support
> **Addressed Issues:** #1, #2, #3, #4, #5

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Infrastructure](#infrastructure)
4. [DynamoDB Schema](#dynamodb-schema)
5. [Discord Integration](#discord-integration)
6. [Authentication & Authorization](#authentication--authorization)
7. [Meal Participation](#meal-participation)
8. [Work Location](#work-location)
9. [Override Update](#override-update)
10. [Security](#security)
11. [Future Enhancements](#future-enhancements)

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

## Meal Participation

### Overview

Employees can view and toggle their meal participation for any eligible date via the `/meal-update` slash command. The bot responds with an interactive embed containing toggle buttons for each meal type. Default participation is **opted-in** — employees explicitly opt out.

### Command: `/meal-update`

```
/meal-update [date:YYYY-MM-DD]
```

- **date** (optional) — Target date. Defaults to today (Asia/Dhaka).
- **Access** — All authenticated users (Employee+).

### Flow

```
1. User types /meal-update [date]
         ↓
2. Lambda validates date:
   - Not in the past
   - Not past cutoff (21:00 Dhaka)
   - Within forward window (7 days)
         ↓
3. Query DynamoDB for user's meal records on that date
         ↓
4. Build embed showing status per meal type + toggle buttons
         ↓
5. Return ephemeral response with embed + buttons
         ↓
6. User clicks a button → component interaction
         ↓
7. Lambda toggles the meal record in DynamoDB
         ↓
8. Return UPDATE_MESSAGE with refreshed embed + buttons
```

### Validation Rules

| Rule | Behavior |
|------|----------|
| Past date | Rejected — "Cannot update past dates" |
| After cutoff (21:00 Dhaka) | Rejected — "Updates for {date} are closed" |
| Beyond forward window | Rejected — "Cannot update dates more than 7 days ahead" |
| Invalid date format | Rejected — "Invalid date format. Use YYYY-MM-DD" |

### Meal Types

Default daily meal types:

| Meal Type | Emoji | Default Status |
|-----------|-------|----------------|
| Lunch | 🍱 | Opted In |
| Snacks | 🍕 | Opted In |

Additional types (activated per-date in future issues):

| Meal Type | Emoji | Trigger |
|-----------|-------|--------|
| Iftar | 🌙 | Ramadan period |
| Event Dinner | 🎉 | Event meal (Issue #13) |
| Optional Dinner | 🍽️ | Special occasions |

### Toggle Behavior

- **No record exists** → Default is opted-in → First toggle creates record with `is_participating: false`
- **Record exists with `true`** → Toggle to `false` (opt out)
- **Record exists with `false`** → Toggle to `true` (opt back in)
- Every toggle stores `updated_by` (Discord ID) and `updated_at` (timestamp)

### Discord Response Format

#### Initial Embed Response

```json
{
  "type": 4,
  "data": {
    "embeds": [{
      "title": "🍽️ Meal Participation",
      "description": "📅 **Wednesday, March 04, 2026**\n\nClick a button below to toggle...",
      "fields": [
        { "name": "🍱 Lunch", "value": "✅ Opted In", "inline": true },
        { "name": "🍕 Snacks", "value": "✅ Opted In", "inline": true }
      ],
      "color": 5793266
    }],
    "components": [{
      "type": 1,
      "components": [
        { "type": 2, "style": 3, "label": "🍱 Lunch ✅", "custom_id": "meal_toggle:USER_ID:2026-03-04:lunch" },
        { "type": 2, "style": 3, "label": "🍕 Snacks ✅", "custom_id": "meal_toggle:USER_ID:2026-03-04:snacks" }
      ]
    }],
    "flags": 64
  }
}
```

#### Button Toggle Response

After clicking a button, the original message is updated in place (type 7 — UPDATE_MESSAGE):
- Embed description includes confirmation: "Updated **🍱 Lunch** → ❌ Opted Out"
- Button style changes: Green (3) → Red (4) or vice versa
- Button label updates: ✅ ↔ ❌

### Button Custom ID Format

```
meal_toggle:{discord_id}:{date}:{meal_type}
```

Example: `meal_toggle:111222333:2026-03-04:lunch`

Security: The handler verifies the clicking user matches the `discord_id` in the custom ID. Users cannot toggle other users' buttons.

---

## Work Location

### Overview

Employees can view and set their work location (Office or Work From Home) for any eligible date via the `/work-location` slash command. The bot responds with an interactive embed containing Office/WFH buttons. Default location is **Office** — employees explicitly switch to WFH. WFH usage is subject to a configurable monthly soft cap (`WFH_MONTHLY_CAP`, default 5).

### Command: `/work-location`

```
/work-location [date:YYYY-MM-DD]
```

- **date** (optional) — Target date. Defaults to today (Asia/Dhaka).
- **Access** — All authenticated users (Employee+).

### Flow

```
1. User types /work-location [date]
         ↓
2. Lambda validates date:
   - Not in the past
   - Not past cutoff (21:00 Dhaka)
   - Within forward window (7 days)
         ↓
3. Query DynamoDB for user's location record on that date
         ↓
4. Build embed showing current location + Office/WFH buttons
         ↓
5. Return ephemeral response with embed + buttons
         ↓
6. User clicks a button → component interaction
         ↓
7. Lambda validates and sets the location in DynamoDB
   (if WFH, checks monthly cap first)
         ↓
8. Return UPDATE_MESSAGE with refreshed embed + buttons
```

### Validation Rules

Same date validation rules as Meal Participation:

| Rule | Behavior |
|------|----------|
| Past date | Rejected — "Cannot update past dates" |
| After cutoff (21:00 Dhaka) | Rejected — "Updates for {date} are closed" |
| Beyond forward window | Rejected — "Cannot update dates more than 7 days ahead" |
| Invalid date format | Rejected — "Invalid date format. Use YYYY-MM-DD" |
| WFH monthly cap exceeded | Rejected — "You have used N/5 WFH days this month" |

### WFH Monthly Cap

- **Default cap:** 5 days per calendar month (configurable via `WFH_MONTHLY_CAP`)
- **Enforcement:** Soft limit — rejects the switch to WFH when at/over cap
- **Counting:** Counts WFH records for the same user in the same calendar month, excluding the date being set (to allow toggling back to Office)
- **Cap = 0:** Disables the cap check entirely

### Location Types

| Location | Emoji | Color | Default? |
|----------|-------|-------|---------|
| Office | 🏢 | Green (`0x57F287`) | Yes |
| Work From Home | 🏠 | Yellow (`0xFEE75C`) | No |

### Toggle Behavior

- **No record exists** → Default is Office → Button shows Office as active (green, disabled)
- **Click WFH** → Creates/updates record with `location: wfh` → WFH active
- **Click Office** → Creates/updates record with `location: office` → Office active
- **Active button** → Green (SUCCESS style), disabled. Inactive → Grey (SECONDARY style), enabled.
- Every change stores `updated_by`, `updated_at`, and `team` (stamped from Discord role)

### Discord Response Format

#### Initial Embed Response

```json
{
  "type": 4,
  "data": {
    "embeds": [{
      "title": "📍 Work Location",
      "description": "📅 **Wednesday, March 04, 2026**\n\nCurrent location: 🏢 **Office**\n\nClick a button below to change your work location.",
      "color": 5763831,
      "footer": { "text": "Default: Office • WFH days count toward monthly cap" }
    }],
    "components": [{
      "type": 1,
      "components": [
        { "type": 2, "style": 3, "label": "🏢 Office ✅", "custom_id": "location_set:USER_ID:2026-03-04:office", "disabled": true },
        { "type": 2, "style": 2, "label": "🏠 Work From Home", "custom_id": "location_set:USER_ID:2026-03-04:wfh", "disabled": false }
      ]
    }],
    "flags": 64
  }
}
```

#### Button Set Response

After clicking a button, the original message is updated in place (type 7 — UPDATE_MESSAGE):
- Embed description includes confirmation: "Updated → 🏠 **Work From Home**"
- Button style changes: active = Green (3, disabled), inactive = Grey (2, enabled)
- Embed color changes: Green for Office, Yellow for WFH

---

## Override Update

### Purpose

Admins and Team Leads can update meal participation and work location **on behalf of another employee** via the `/override-update` slash command. This is intended for correcting missed entries or handling situations where an employee cannot update their own records.

### Command: `/override-update`

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `employee` | USER | Yes | The target employee (Discord user mention) |
| `date` | STRING | No | Target date (`YYYY-MM-DD`), defaults to today |

### Authorization & Team-scoping

| Role | Scope |
|------|-------|
| **Admin** | Can override any employee across all teams |
| **Team Lead** | Can only override employees within their own team |
| **Employee** | Cannot use this command |

- Minimum role requirement: `UserRole.TEAM_LEAD` (hierarchy level 1+)
- Team-scoping is enforced in `OverrideService.check_team_scope()`
- The target employee's team is derived from their Discord roles via `extract_team_from_roles()`

### Flow

```
/override-update employee:@Target date:2026-03-05
  ↓
Auth gate: role >= TEAM_LEAD?
  ↓
Team scope: TL same team? Admin always?
  ↓
Build embed + buttons showing current state
  ↓
User clicks meal/location button
  ↓
OverrideService.override_meal() / override_location()
  ↓
Updated message with new state + confirmation
```

### Button Custom ID Format

**Meal buttons:**
```
override_meal:{actor_id}:{target_id}:{date}:{meal_type}:{in|out}
```

**Location buttons:**
```
override_loc:{actor_id}:{target_id}:{date}:{location_type}
```

### Security

- Only the **original actor** (who ran `/override-update`) can click the override buttons
- Button clicks by other users are rejected with an ephemeral error
- The `actor_id` is encoded in the custom ID and verified on every button interaction

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

- **Headcount Reporting** (Issue #6) — `/headcount-summary` and `/team-summary` commands
- **EventBridge Integration** — Scheduled daily summary generation
- **Team-based Queries** — Team name stamped on records at write time; team queries use `Query` + `FilterExpression`. TL's team derived from interaction payload roles (zero extra API calls). GSI can be added later if filter cost becomes a concern at scale.
- **Web Dashboard** — Separate web interface for admins (Task 3)
- **Discord Announcements** — Auto-post summaries to channels
- **OAuth2 Flow** — For web dashboard authentication and discord and lambda request processing

---

*This documentation will be updated as new issues are implemented.*

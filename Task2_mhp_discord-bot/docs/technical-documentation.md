# MHP Discord Bot — Technical Documentation

> **Version:** 1.0.0  
> **Last Updated:** 2026-03-03  
> **Status:** Issue #1 Complete — Serverless Infrastructure Setup

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Infrastructure](#infrastructure)
4. [DynamoDB Schema](#dynamodb-schema)
5. [Discord Integration](#discord-integration)

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

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_PUBLIC_KEY` | Discord app public key | (required) |
| `DISCORD_APPLICATION_ID` | Discord application ID | (required) |
| `DISCORD_BOT_TOKEN` | Discord bot token | (required) |
| `DISCORD_GUILD_ID` | Discord server ID | (required) |
| `DYNAMODB_TABLE_NAME` | DynamoDB table name | `mhp-dev-data` |
| `S3_BUCKET` | S3 bucket name | `mhp-dev-reports` |
| `CUTOFF_TIME` | Meal update cutoff (Dhaka) | `21:00` |
| `WFH_MONTHLY_CAP` | WFH days per month | `5` |
| `FORWARD_PLANNING_DAYS` | Max days ahead to book | `7` |
| `TIMEZONE` | timezone | `Asia/Dhaka` |

---

## DynamoDB Schema

### Design Principles

- **Single-table design** — All entities in one DynamoDB table
- **No GSIs** — All access patterns use primary key queries
- **Partition by date** — Most common queries are date-based

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
| Get all locations for date | Query | `PK = DATE#2026-02-26#LOCATION` |
| Get user profile | Get | `PK = USER#123`, `SK = PROFILE` |
| Get special day | Get | `PK = SPECIALDAY#2026-02-26` |
| Get policy | Get | `PK = POLICY#cutoff_time` |

### Data Models

#### User

```python
class User:
    discord_id: str      # Primary identifier
    name: str           # Display name
    email: str          # Email (optional)
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
    updated_by: str       # Who made the update
    updated_at: datetime
    reason: str           # Optional reason for change
```

#### WorkLocation

```python
class WorkLocation:
    user_id: str           # Discord user ID
    date: date            # Location date
    location: WorkLocationType  # office, wfh
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
4. **Process & Respond** — Lambda processes request and returns response

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


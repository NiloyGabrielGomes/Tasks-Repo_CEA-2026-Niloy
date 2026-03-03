# MHP Discord Bot — Technical Documentation

> **Version:** 1.0.0  
> **Last Updated:** 2026-03-03  
> **Status:** Issue #1 Complete — Serverless Infrastructure Setup

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Infrastructure](#infrastructure)

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


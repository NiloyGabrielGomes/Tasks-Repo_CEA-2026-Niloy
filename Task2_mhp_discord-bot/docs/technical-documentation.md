# MHP Discord Bot — Technical Documentation

> **Version:** 1.0.0  
> **Last Updated:** 2026-03-03  
> **Status:** Issue #1 Complete — Serverless Infrastructure Setup

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)

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


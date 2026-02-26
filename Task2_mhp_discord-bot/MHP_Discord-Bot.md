# Discord Bot for Meal Headcount Planner (MHP)

```
Niloy Gabriel Gomes
Feb 26, 2026
Status: Draft - Pending Review
```
---

## Summary
This document outlines the development of a Discord bot for Meal Headcount Planner (MHP). The bot will provide a user-friendly interface/discord message for employees to view and manage their meal participation, as well as for team leads and admins to manage meal participation for their teams and employees, respectively. It also provides the development specification for the meal headcount reporting and other information/statistics, including, work location splits and special day information. The bot will be used to notify employees about their meal participation, as well as for team leads and admins to manage meal participation for their teams and employees.

---

## Problem statement
* Employees currently lack a fast, integrated way to update their meal preferences and work locations seamlessly within their daily communication tool (Discord).
* Administrators and Team Leads struggle to quickly gather headcount summaries for specific dates, leading to inefficiencies in meal planning, tracking, and logistics.
* The existing system lacks a functional, component-based web dashboard that provides real-time, shared-state updates for effective monitoring.

---

## Goals and non-goals

### Goals
- Implement a Discord bot for employees to self-update meal participation and work location (Office/WFH) for a given date.
- Enable Team Leads and Admins/Logistics to fetch daily rollups and summaries via the Discord bot.
- Develop a component-based web dashboard with live updates, shared state, and rich data views (meal totals, work location splits, special days).
- Implement async processing for daily summary generation triggered by admins.
- Cutoff time configurable by admin (default: 9 PM Dhaka time)

### Non-goals
* Building a completely new identity management system (we will rely on existing auth/Discord IDs).
* Mobile application development (the web dashboard will handle standard browser viewing, Discord bot handles mobile implicitly).
* Automated ordering to logistics team (only tracking the headcount).

---

## Tech stack and rationale (short)
- **Backend language/runtime**: Python 3.12.x – Language of choice for backend and discord bot.
- **Framework**: FastAPI - Native async support crucial for real-time WebSocket connections
- **Data store**: S3 file storage – Temporary data storage. DynamoDB - Planned for future storage integration
- **Infra/deploy**: AWS – ensures production-grade deployment, simple CI/CD pipeline, and reproducible infrastructure.
- **Integrations**: Discord API (discord.js) – directly interfaces with user input and handles interactive components (buttons, slash commands).

---


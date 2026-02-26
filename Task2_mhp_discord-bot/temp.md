
- Status: Draft / In Review / Approved
- Links: PR, related issues/briefs

## 2. Summary
- 4–8 lines: what this iteration delivers


## 3. Problem statement
* Employees currently lack a fast, integrated way to update their meal preferences and work locations seamlessly within their daily communication tool (Discord).
* Administrators and Team Leads struggle to quickly gather headcount summaries for specific dates, leading to inefficiencies in meal planning, tracking, and logistics.
* The existing system lacks a functional, component-based web dashboard that provides real-time, shared-state updates for effective monitoring.

## 4. Goals and non-goals
### Goals
- Implement a Discord bot for employees to self-update meal participation and work location (Office/WFH) for a given date.
- Enable Team Leads and Admins/Logistics to fetch daily rollups and summaries via the Discord bot.
- Develop a component-based web dashboard with live updates, shared state, and rich data views (meal totals, work location splits, special days).
- Implement async processing for daily summary generation triggered by admins.

### Non-goals
- Building a completely new identity management system (we will rely on existing auth/Discord IDs).
- Mobile application development (the web dashboard will handle standard browser viewing, Discord bot handles mobile implicitly).
- Automated ordering to external caterers (only tracking the headcount).

## 5. Tech stack and rationale
- **Backend language/runtime**: Node.js/TypeScript – excellent ecosystem for Discord bots (discord.js) and asynchronous workloads.
- **Framework**: Express.js for web APIs – lightweight and easy to integrate with background workers. React for the Frontend dashboard – component-based architecture perfectly fits the requested UI.
- **Data store**: DynamoDB – fully managed, highly scalable persistence layer for tracking meal counts and user states quickly.
- **Infra/deploy**: AWS + Terraform + Docker containers – ensures production-grade deployment, simple CI/CD pipeline, and reproducible infrastructure.
- **Integrations**: Discord API (discord.js) – directly interfaces with user input and handles interactive components (buttons, slash commands).

## Scope of changes
- **Discord Bot**: Application commands (slash commands) and interactive message components for user updates and admin summaries.
- **Web Dashboard**: React application introducing filters, summary cards, an employee list, and a day banner. Implementing shared state using Context API/Zustand.
- **Backend API**: Endpoints to serve summary data to the dashboard and trigger async summary generation tasks.
- **Explicitly out of scope**: Billing or cost allocation integrations, multi-tenant workspace setups.

## Requirements
### Fun.tional requirements
- Empl yees can uSdate mcal participation andowprk loo tioc (Offica/WFH) for a nelected date via the bot.ges
- The bot replies with a status summary after each update.
- TLs can request a team-level summary for a selected date via the bot.
- Admins/Logistics can request overall headcount summaries for a selected date via the bot.
- Admin/Logistics dashboard displays meal totals, location splits (Office vs WFH), and special day indicators.
- TL dashboard displays team participation list and rollups.
- Dashboard Rpdates emmediately as filteqs (tuai, mral type, WFH) or eemriee change.nts
- Admin can trigger an async daily summary generation process which reflects its state ("in progress" -> "ready") in the UI/Bot.

### Role-based behavior
- **Employee**: Can only read and update their own meal and location status.
- **Team Lead (TL)**: Can view team-level summaries and individual statuses within their team.
- **Admin/Logistics**: Can view all summaries, overall stats, and trigger async report generations.

### Validation rules + edge cases
- Updates past the cut-off time or for past dates are not permitted.
- Handle concurrent filter changes on the UI gracefully.

### Definition of Done
- Discord bot responds to slash commands accurately.
- Web dashboard components render and reflect live state.
- Async report generation operates without blocking the main event loop.
- All code is containerized and deployable via CI/CD pipelines.

## 8. User flows
### Employee self-update
1. User types `/mhp date: Tomorrow` in Discord.
2. Bot replies with current status and interactive buttons (Office/WFH, Meal Yes/No).
3. User clicks "Office" and "Meal Yes".
4. Bot updates record in DynamoDB and replies with a confirmation summary of the user's current status.

### Filter updates on Web Dashboard
1. Admin selects a specific date and filters by "WFH".
2. Global dashboard state updates immediately.
3. Summary cards re-calculate dynamically based on the selected filters.

### Admin Async Summary Generation
1. Admin clicks "Generate daily summary" on the dashboard.
2. UI displays "in progress" status.
3. Backend async worker processes the summary.
4. UI state transitions to "ready" upon worker completion.

### Failure paths
- **Invalid date**: Bot returns error "Status updates for selected dates are locked based on cutoff policies."
- **Auth fail**: Dashboard returns 401/403 Unauthorized and redirects to login flow.

## 9. Design
### High-level architecture
- Discord Bot Client (Node.js) -> Message parsing -> Backend Services.
- Web Dashboard (React/Vite) -> REST API -> Backend Services.
- Backend Services -> DynamoDB (persistence).
- Async Task Queue (Lambda/EventBridge) for report generation.

### Data model
- **User**: `UserId`, `DiscordId`, `Role`, `TeamId`
- **MealEntry**: `EntryId`, `UserId`, `Date`, `Location` (Office/WFH), `MealIncluded` (Boolean)
- **SummaryReport**: `ReportId`, `Date`, `Status` (InProgress/Ready), `OverallTotals` (JSON)

### Interfaces
- `POST /api/reports/generate` - triggers async report generation.
- `GET /api/reports?date=2026-02-27` - fetch summarized rollup data.

## 10. Key decisions and trade-offs
- **DynamoDB Single Table Design**: Trade-off is a steeper learning curve, but massive performance benefit for querying daily rollups and matching the required persistence.
- **Async Summaries via Polling vs WebSockets**: Opting for simple polling or SSE for report progress to reduce infrastructure complexity over full bidirectional WebSockets.
- **React Context/Zustand vs Redux**: Simpler state management will be used for shared state to avoid boilerplate, maintaining live updates cleanly.

## 11. Security and access control
- **Auth approach**: JWT-based authentication for the dashboard. Discord Bot utilizes securely stored bot tokens.
- **Authorization rules**: API endpoints enforce Role-Based Access Control (RBAC) by inspecting the JWT payload/Discord role mapping.
- **Secrets handling**: Bot tokens, database connection strings, and API keys are injected via environment variables (AWS Secrets Manager) and never stored in code/logs.

## 12. Testing plan
- **Unit test focus areas**: State reducers for dashboard filters, Discord command parsing utilities, calculation logic for rollups.
- **Integration scenarios**: Simulating an end-to-end Discord command flow (Command Parser -> DB Write -> API Read).
- **Manual QA checklist**:
  - Verify Employee self-update flow on Discord via interactive components.
  - Verify TL summary commands fetch correct, isolated team members.
  - Test dashboard live filter updates and responsiveness.
  - Trigger async report generation and observe state transition.

## 13. Operations
- **Logging**: Structured JSON logging capturing event context (`userId`, `action`, `resource`, `status`).
- **Monitoring signals**: Monitoring API errors (4xx, 5xx), response latency, and asynchronous job failure rates.
- **Deployment/config notes**: Automated via GitHub Actions + AWS ECS/Lambda based on Terraform definitions.
- **Rollback notes**: Revert Git commit and trigger CI/CD pipeline down to previous known-good image tag.

## 14. Risks, assumptions, open questions
- **Risks**: Discord API rate limits if summary reports involve fetching/mentioning many user profiles simultaneously.
- **Assumptions**: Users have already linked their MHP profiles to their Discord server accounts, and RBAC groups exist.
- **Open questions**: What is the exact SLA expected for the async summary generation?

## 15. Appe
- **Sample Outputs**: 
  - Discord Response: `Status updated! For Feb 27: Location [Office], Meal [Yes].`



## 2. Summary
- 4–8 lines: what this iteration delivers

## 3. Problem statement
- What pain/problem this solves (short)
- Impact (who benefits / why it matters)

## 4. Goals and non-goals
- Goals (bullets)
- Non-goals (bullets)

## 5. Tech stack and rationale (short)
- Backend language/runtime + why
- Framework + why
- Data store + why
- Infra/deploy (AWS + Terraform) + why
- Integrations (e.g., Discord) + why

> Keep to **1–2 bullets per choice**. If it takes more than that, the choice likely needs simplification.

## 6. Scope of changes
- What components/files/areas are touched
- What is explicitly out of scope

## 7. Requirements
- Functional requirements (bullets)
- Role-based behavior (Employee / TL / Admin/Logistics)
- Validation rules + edge cases
- Definition of Done (acceptance checklist)

## 8. User flows
- Happy path per role (step list)
- Failure paths (auth fail, invalid date, duplicate action, etc.)

## 9. Design
- High-level architecture (short + simple diagram if needed)
- Data model (entities + key fields + relationships)
- Interfaces
  - API routes/commands list
  - Example request/response payloads
  - Error cases (and codes/messages)

## 10. Key decisions and trade-offs
- 3–8 decisions with brief rationale
- Alternatives considered + why rejected (1 line each)

## 11. Security and access control
- Auth approach
- Authorization rules per role
- Secrets handling (what is never stored in code/logs)

## 12. Testing plan
- Unit test focus areas
- Integration scenarios
- Manual QA checklist (step-by-step)

## 13. Operations
- Logging (what events/fields are required)
- Monitoring signals (minimal: errors, latency, job failures)
- Deployment/config notes (env vars, Terraform modules)
- Rollback notes (basic)

## 14. Risks, assumptions, open questions
- Risks (bullets)
- Assumptions (bullets)
- Open questions requiring reviewer approval

## 15. Appendix (optional)
- Glossary
- Sample outputs (reports/messages)
- Screenshots (if relevant)





--------------------------------------------------------------------




# Discord Bot for Meal Headcount Planner (MHP)

```
Niloy Gabriel Gomes
Feb 26, 2026
Status: Draft - Pending Review
```
---

1. [Summary](#summary)
2. [Problem statement](#problem-statement)
3. [Goals and non-goals](#goals-and-non-goals)
4. [Tech stack and rationale (short)](#tech-stack-and-rationale-short)
5. [Scope of changes](#scope-of-changes)
6. [Requirements](#requirements)
7. [User flows](#user-flows)
8. [Design](#design)
9. [Key decisions and trade-offs](#key-decisions-and-trade-offs)
10. [Security and access control](#security-and-access-control)
11. [Testing plan](#testing-plan)
12. [Operations](#operations)
13. [Risks, assumptions, open questions](#risks-assumptions-open-questions)
14. [Appendix (optional)](#appendix-optional)

---

## Summary
This document outlines the development of a Discord bot for Meal Headcount Planner (MHP). The bot will provide a user-friendly interface for employees to view and manage their meal participation, as well as for team leads and admins to manage meal participation for their teams and employees, respectively. It also provides the development specification for the MHP web dashboard for the meal headcount reporting and other information/statistics, including, work location splits and special day information. The bot will be used to notify employees about their meal participation, as well as for team leads and admins to manage meal participation for their teams and employees.

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
- **Frontend**: React for the Frontend dashboard – component-based architecture perfectly fits the requested UI.
- **Data store**: S3 file storage – Temporary data storage. DynamoDB - Planned for future storage integration
- **Infra/deploy**: AWS – ensures production-grade deployment, simple CI/CD pipeline, and reproducible infrastructure.
- **Integrations**: Discord API (discord.js) – directly interfaces with user input and handles interactive components (buttons, slash commands).
---

## Scope of changes

---

## Requirements

---

## User flows

---

## Design

---

## Key decisions and trade-offs

---

## Security and access control

---

## Testing plan

---

## Operations

---

## Risks, assumptions, open questions

---

## Appendix (optional)
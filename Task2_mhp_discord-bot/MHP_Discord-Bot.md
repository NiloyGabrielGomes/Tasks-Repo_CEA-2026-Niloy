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

### Non-goals
* Building a completely new identity management system (we will rely on existing auth/Discord IDs).
* Mobile application development (the web dashboard will handle standard browser viewing, Discord bot handles mobile implicitly).
* Automated ordering to external caterers (only tracking the headcount).

---

## Tech stack and rationale (short)

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
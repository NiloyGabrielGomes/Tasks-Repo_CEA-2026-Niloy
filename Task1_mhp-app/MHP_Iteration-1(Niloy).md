# Meal Headcount Planner (MHP)

```
Niloy Gabriel Gomes
Feb 18, 2026
Status: Draft - Pending Review
```

- [Overview](#overview)
   - Tech Stack
   - Summary
   - Problem Statement
- [Goals and Non-Goals](#goals-and-non-goals)
   - Goals
   - Non-Goals
- [Requirements](#requirements)
   - Functional Requirements
   - Non-Functional Requirements
   - Constraints
- [Development Steps](#development-steps)
   - 1. Project Setup
   - 2. Data Models and Storage
   - 3. User Flows
   - 4. Authentication and Authorization
   - 5. Backend API Development
   - 6. Frontend Development
   - 7. Other Logic Implementation
   - 8. Documentation, Testing and Validation
   - 9. Local Deployment/Operations
- [Risks, Assumptions, and Open Questions](#risks-assumptions-and-open-questions)
- [Key Design Decisions](#key-design-decisions)

---

## Overview

Build a web app to track daily meal participation for 100+ employees, replacing Excel-based
tracking.

### Tech Stack

```
Frontend: React + Vite
Backend API: Python (FastAPI)
Authentication: Basic login with roles (Employee / Team Lead / Admin/Logistics)
Storage: File-based JSON (to be migrated to a database in a future iteration)
Packaging: Run locally
Development Tools:
● Backend: pip + requirements.txt
● Frontend: npm or pnpm
● CORS middleware enabled for local development
```
### Summary

```
This document contains a comprehensive development roadmap for the Meal Headcount
Planner (MHP). It covers self-service meal participation, role-based access control,
team/department visibility, special day controls, improved headcount reporting with
Office/WFH splits, live updates, daily announcement drafts, work location tracking,
and company-wide WFH period management. It outlines the technical implementation
using Python-FastAPI for the backend and React for the frontend, including data
models, API endpoints, and UI components required for these features. The plan
breaks down the development process into actionable phases, with specific
implementation details for each layer of the stack.
```
### Problem Statement
The organization currently uses a manual Excel-based process to track daily meal participation for 100+ employees. This approach presents several critical challenges, like operational ineffeciencies, data quality issues, and potential negative business impacts due to inaccurate head counts. The proposed solution targets to alleviate these challenges by increasing efficiency and accuracy.

---

## Goals and Non-Goals

### Goals

**Primary Goals:**

1. **Self-Service Meal Participation**
   - Employees can view and toggle their daily meal opt-in/out status
   - Employees default to "opted-in" for all meals

2. **Role-Based Access Control**
   - Three-tier role system: Employee, Team Lead, Admin/Logistics
   - Each role has scoped permissions for viewing and modifying data

3. **Administrative Override**
   - Team Leads and Admins can update participation on behalf of users
   - All overrides are recorded with who made the change and a timestamp for audit

4. **Headcount Reporting**
   - Real-time headcount totals by meal type, team, overall total, and Office vs WFH split
   - Headcount updates immediately when participation changes

5. **Team-Based Visibility**
   - Employees can see which team they belong to
   - Team Leads can view participation for their own team for the day
   - Admin/Logistics can view participation across all teams

6. **Bulk and Exception Handling**
   - Team Leads/Admin can apply bulk actions for their scope (e.g., mark a group as opted out due to offsite/event)

7. **Special Day Controls**
   - Admin/Logistics can mark a day as Office Closed, Government Holiday, or Special Celebration Day (with a note)
   - System adjusts meal availability based on the day type

8. **Live Updates (No Refresh)**
   - Headcount totals update immediately when any employee changes participation, without page reload

**Secondary Goals:**

9. **Daily Announcement Draft**
   - Logistics/Admin can generate a copy/paste-friendly message for a selected date
   - Message includes meal-wise totals and highlights special-day notes

10. **Work Location Tracking**
    - Employees can set their work location for a selected date: Office / WFH
    - Team Leads / Admin can correct missing work-location entries

11. **Company-Wide WFH Period**
    - Admin/Logistics can declare a date range as "WFH for everyone"
    - During the declared period, the system treats employees as WFH by default for reporting

12. **Extensible Architecture**
    - Design architecture to support future database migration
    - Create extensible data models
    - Implement authentication framework for future features

### Non-Goals

**Features Deferred to Future Iterations:**

1. **Advanced Planning Features**
   - Weekly/monthly calendar view
   - Advance meal scheduling
   - Recurring participation patterns

2. **Cutoff Time Enforcement**
3. **Notifications and Reminders** (push/email[optional])
4. **Analytics and Reporting** (historical logs, charts)
5. **Advanced User Management** (self-service role changes)


---

## Requirements

### Functional Requirements

#### FR-1: User Authentication
- **FR-1.1:** Users must be able to log in with email and password
- **FR-1.2:** System must issue JWT tokens upon successful authentication
- **FR-1.3:** Users must be able to register themselves as "Employee" role

#### FR-2: User Authorization
- **FR-2.1:** System must enforce role-based access control (Employee, Team Lead, Admin)
- **FR-2.2:** Employees can only view and modify their own participation
- **FR-2.3:** Admins can view and modify any user's participation, Team Leads can view and modify their team members' participation

#### FR-3: Meal Participation Management
- **FR-3.1:** Employees must default to "opted-in" for all meals
- **FR-3.2:** Employees must be able to opt-out of specific meals
- **FR-3.3:** Employees must be able to opt back in after opting out

#### FR-4: Admin Participation Override
- **FR-4.1:** Team Leads and Admins can update participation on behalf of users
- **FR-4.2:** System must record who made the administrative update
- **FR-4.3:** Updates must include timestamp for audit purposes

#### FR-5: Headcount Reporting
- **FR-5.1:** System must calculate real-time headcount for each meal type
- **FR-5.2:** Headcount must update immediately when participation changes
- **FR-5.3:** System must show total employee count alongside meal counts

#### FR-6: User Management
- **FR-6.1:** Admins can create new users with any rolem view list of all users, deactive users (soft delete), update user information (name, role, department)
- **FR-6.2:** Users can view their own profile information

#### FR-7: Team-Based Visibility
- **FR-7.1:** Employees can see which team they belong to on their dashboard
- **FR-7.2:** Team Leads can view participation status for all members of their own team for a given day
- **FR-7.3:** Admin/Logistics can view participation across all teams with team-level grouping

#### FR-8: Bulk and Exception Handling
- **FR-8.1:** Team Leads can apply bulk opt-out actions for members within their team scope (e.g., offsite/event)
- **FR-8.2:** Admins can apply bulk opt-out actions across any team or the entire organization
- **FR-8.3:** Bulk actions must record who initiated them and include timestamps for audit

#### FR-9: Special Day Controls
- **FR-9.1:** Admin/Logistics can mark a date as one of: Office Closed, Government Holiday, or Special Celebration Day
- **FR-9.2:** Special Celebration Day entries must support an optional note/description
- **FR-9.3:** When a day is marked as "Office Closed" or "Government Holiday", the system must disable meal participation for that day
- **FR-9.4:** Special day status must be visible to all users on the relevant date's view

#### FR-10: Improved Headcount Reporting
- **FR-10.1:** Headcount totals must be available broken down by meal type
- **FR-10.2:** Headcount totals must be available broken down by team
- **FR-10.3:** System must display overall total headcount
- **FR-10.4:** System must display Office vs WFH split in headcount reporting

#### FR-11: Live Updates
- **FR-11.1:** When any employee updates their meal participation, all visible headcount totals must update immediately without requiring a page reload
- **FR-11.2:** Live updates must apply to Admin dashboard, Team Lead dashboard, and any headcount display

#### FR-12: Daily Announcement Draft
- **FR-12.1:** Logistics/Admin can generate a copy/paste-friendly text message for a selected date
- **FR-12.2:** The generated message must include meal-wise headcount totals
- **FR-12.3:** The generated message must highlight any special-day notes (holiday, office closed, celebration)

#### FR-13: Work Location Management
- **FR-13.1:** Employees can set their work location for a selected date as either "Office" or "WFH"
- **FR-13.2:** Team Leads can view and correct missing work-location entries for their team members
- **FR-13.3:** Admins can view and correct missing work-location entries for any employee

#### FR-14: Company-Wide WFH Period
- **FR-14.1:** Admin/Logistics can declare a date range as "WFH for everyone"
- **FR-14.2:** During a declared WFH period, the system must treat all employees as WFH by default for reporting purposes
- **FR-14.3:** Individual employees can still override their location if they come to the office during a WFH period

### Non-Functional Requirements

#### NFR-1: Performance
#### NFR-2: Usability
#### NFR-3: Reliability
#### NFR-4: Security
- **NFR-4.1:** Passwords must be hashed using bcrypt (never stored in plain text)
- **NFR-4.2:** JWT tokens must be signed and verified
- **NFR-4.3:** API endpoints must validate all input data
- **NFR-4.4:** Sensitive data (passwords) must never appear in API responses
- **NFR-4.5:** CORS must be configured to allow only frontend origin

#### NFR-5: Maintainability
#### NFR-6: Scalability (Future-Proofing)

### Constraints

#### Technical Constraints
- **TC-1:** Must work on standard browsers (Chrome, Firefox, Edge - latest 2 versions)

#### Business Constraints
- **BC-1:** Development timeline: Feb 10th, 2026 for Iteration 1
- **BC-1.1:** Development timeline: Feb 23th, 2026 for Iteration 2 ← Iteration 2
- **BC-2:** Single developer resource

#### User Constraints
- **UC-1:** All employees must have computer/device access
- **UC-2:** Users must have company email addresses

---

## Development Steps

### System Architecture

```

                        CLIENT LAYER                          
                                                              
  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   
  │ Browser  │  │ Browser  │  │ Browser  │  │ Browser  │   
  │(Employee)│  │(Team Lead│  │ (Admin)  │  │ (Mobile) │   
  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   
       │             │             │             │           
       └─────────────┴─────────────┴─────────────┘           
                           │                                   
                       HTTPS/REST                               
                           │
                           │
                           │
                   APPLICATION LAYER                          
          ┌───────────────▼────────────────┐                 
          │   React Frontend (SPA)         │                
          │      Port: 5173 (dev)          │               
          │                                │              
          │                                │                 
          │  Services:                     │                 
          │  └─ api.js (Axios)             │                 
          │                                │                 
          │  State:                        │                 
          │  └─ AuthContext (JWT token)    │                 
          └───────────────┬────────────────┘                 
                          │                                   
                     HTTP (Axios)                             
                          │
                      API LAYER                               
          ┌───────────────▼────────────────┐                 
          │   FastAPI Backend              │                 
          │      Port: 8000                │                 
          │                                │                 
          │  ┌──────────────────────────┐  │                 
          │  │   CORS Middleware        │  │                 
          │  └──────────────────────────┘  │                 
          │  ┌──────────────────────────┐  │                 
          │  │   Auth Middleware (JWT)  │  │                 
          │  └──────────────────────────┘  │                 
          │  ┌──────────────────────────┐  │                 
          │  │   Routers:               │  │                 
          │  │   ├─ auth.py             │  │                 
          │  │   ├─ meals.py            │  │                 
          │  │   ├─ users.py            │  │                 
          │  │   ├─ teams.py            │  │
          │  │   ├─ special_days.py     │  │
          │  │   ├─ work_locations.py   │  │
          │  │   ├─ sse.py              │  │
          │  │   └─ announcements.py    │  │  
          │  └──────────────────────────┘  │                 
          │  ┌──────────────────────────┐  │                 
          │  │   Business Logic:        │  │                 
          │  │   ├─ auth.py             │  │                 
          │  │   ├─ models.py           │  │                 
          │  │   └─ schemas.py          │  │                 
          │  └──────────────────────────┘  │                 
          └────────────────┬───────────────┘                 
                           │
                      DATA LAYER                               
          ┌───────────────▼────────────────┐                 
          │   Storage Module               │                 
          │      (storage.py)              │                 
          │                                │                 
          │  Functions:                    │                 
          │  ├─ load_json()                │                 
          │  ├─ save_json()                │                 
          │  ├─ get_user_by_email()        │                 
          │  ├─ update_participation()     │                 
          │  ├─ get_headcount_by_date()    │                 
          │  ├─ get_team_participation()   │
          │  ├─ bulk_update_participation()│
          │  ├─ get_special_day()          │
          │  ├─ get_work_location()        │
          │  └─ get_wfh_periods()          │  
          └───────────────┬────────────────┘                 
                          │                                   
                    JSON File I/O                             
                          │                                   
          ┌───────────────▼────────────────┐                 
          │   File System                  │                
          │                                │                 
          │  /backend/data/                │                 
          │  ├─ users.json                 │                 
          │  ├─ meal_participation.json    │                 
          │  ├─ special_days.json          │
          │  ├─ work_locations.json        │
          │  └─ company_wfh_periods.json   │  
          └────────────────────────────────┘                 
```

### 1. Project Setup

Initialize project repository with chosen tech stack; repository name:
**Tasks-Repo_CEA-2026-Niloy/Task1_mhp-app**. Proceed with setting up the following
folder structure:
```
mhp-app/
├── backend/
│ ├── app/
│ │ └── routers/
│ ├── data/
│ │ ├── users.json
│ │ ├── meal_participation.json
│ │ ├── meal_config.json
│ │ ├── special_days.json
│ │ ├── work_locations.json
│ │ └── company_wfh_periods.json
│ ├── requirements.txt
│ └── .env
├── frontend/
│ ├── src/
│ │ ├── components/
│ │ ├── pages/
│ │ ├── services/
│ │ ├── context/
│ │ ├── App.jsx
│ │ └── main.jsx
│ ├── package.json
│ └── .env
└── README.md
```


Configure development environment and dependencies and create the .env template for
configuration.

### 2. Data Models and Storage

Define the following models in models.py using the Pydantic validation library:
● User - id, name, email, password_hash, role, team, is_active, created_at
● MealParticipation - id, user_id, date, meal_type, is_participating, updated_at
● MealType(enum) - Lunch, Snacks, Iftar, EventDinner, OptionalDinner
   (Note: Iftar is not a default meal. Special meals like Iftar will be handled through admin configuration)
● UserRole(enum) - Employee, TeamLead, Admin

● SpecialDay - id, date, day_type, note, created_by, created_at
● DayType(enum) - OfficeClosed, GovernmentHoliday, SpecialCelebration
● WorkLocation - id, user_id, date, location, updated_by, updated_at
● WorkLocationType(enum) - Office, WFH
● CompanyWFHPeriod - id, start_date, end_date, declared_by, created_at

Implement file-based JSON storage utilities in storage.py. Use {load_json(filename)} to
read data, {save_json(filename, data)} to write data, and {get_by_id();
create(); update(); delete()} as helpers. Create seed data for testing purposes.

Storage files:
● users.json - Stores user records
● meal_participation.json - Stores per-user per-date meal participation
● meal_config.json - Stores meal type configuration
● special_days.json - Stores special day entries (office closed, holidays, celebrations)
● work_locations.json - Stores per-user per-date work location selections
● company_wfh_periods.json - Stores admin-declared company-wide WFH date ranges

### 3. User Flows

Flow 1: Employee Daily Check-in and Opt-out
```
┌─────────────────────────────────────────────────────────────┐
│                    Employee Daily Workflow                   │
└─────────────────────────────────────────────────────────────┘

1. Employee arrives at work
   │
   ├─> Opens web browser
   │
   ├─> Navigates to MHP application (http://mhp.company.local)
   │
   └─> LOGIN PAGE
       │
       ├─> Enters email: john.doe@company.com
       ├─> Enters password: ********
       └─> Clicks "Login"
           │
           ├─> [System validates credentials]
           ├─> [System issues JWT token]
           └─> [Redirect to Employee Dashboard]
               │
               └─> EMPLOYEE DASHBOARD
                   │
                   ├─> Views today's date: "Thursday, February 6, 2026"
                   │
                   ├─> Sees meal participation status:
                   │   ┌─────────────────────────────────┐
                   │   │ ✓ Lunch         [Opted In ]    │
                   │   │ ✓ Snacks        [Opted In ]    │
                   │   │ ✓ Iftar         [Opted In ]    │
                   │   │    ├─> Applicable  if enabled   │
                   │   │        by admin config          │
                   │   │ ✓ Event Dinner  [Opted In ]    │
                   │   │ ✓ Optional Dinner [Opted In ]  │
                   │   └─────────────────────────────────┘
                   │
                   ├─> Decision Point: Need to opt-out?
                   │   │
                   │   ├─> YES: Won't attend lunch today
                   │   │   │
                   │   │   ├─> Clicks toggle next to "Lunch"
                   │   │   │
                   │   │   ├─> [API Call: PUT /api/meals/participation]
                   │   │   │
                   │   │   ├─> [System updates participation record]
                   │   │   │   - Sets is_participating = false
                   │   │   │   - Records updated_by = john.doe@company.com
                   │   │   │   - Records timestamp
                   │   │   │
                   │   │   ├─> [Response: 200 OK]
                   │   │   │
                   │   │   └─> UI Updates:
                   │   │       ┌─────────────────────────────────┐
                   │   │       │ ✗ Lunch         [Opted Out]    │
                   │   │       │ ✓ Snacks        [Opted In ]    │
                   │   │       │ ✓ Iftar         [Opted In ]    │
                   │   │       │   ├─> Applicable  if enabled   │
                   │   │       │        by admin config         │
                   │   │       │ ✓ Event Dinner  [Opted In ]    │
                   │   │       │ ✓ Optional Dinner [Opted In ]  │
                   │   │       └─────────────────────────────────┘
                   │   │       │
                   │   │       └─> Shows success message: "Lunch participation updated"
                   │   │
                   │   └─> NO: All meals correct
                   │       │
                   │       └─> Closes browser
                   │
                   └─> Total time: ~20-30 seconds 

Alternative Flow 1A: Employee Changes Mind
   │
   ├─> Previously opted out of Lunch
   ├─> Plans change, wants to attend
   └─> Clicks toggle to opt back in
       │
       └─> [Same API call with is_participating: true]
           │
           └─> Success: Back to opted-in status

Alternative Flow 1B: Network Error
   │
   ├─> Employee clicks toggle
   ├─> [API request fails - network down]
   └─> Error message: "Unable to update. Please try again."
       │
       └─> Employee can retry or contact support

```

Flow 2: Team Lead Managing Team Member's Participation

```
┌─────────────────────────────────────────────────────────────┐
│              Team Lead Exception Handling Workflow           │
└─────────────────────────────────────────────────────────────┘

Scenario: Team member calls in sick, can't access system

1. Team member calls Team Lead
   │
   ├─> "I'm sick today, won't make it to the office"
   │
   └─> Team Lead opens MHP application
       │
       └─> LOGIN as Team Lead
           │
           └─> TEAM LEAD DASHBOARD
               │
               ├─> Views: "Manage Team Participation"
               │
               ├─> Searches for team member:
               │   ┌─────────────────────────────────────┐
               │   │ Search: [John Doe        ] [Search]│
               │   └─────────────────────────────────────┘
               │
               ├─> Results:
               │   ┌─────────────────────────────────────────────────────┐
               │   │ John Doe - Engineering                              │
               │   │ Today's Participation:                              │
               │   │   ✓ Lunch    ✓ Snacks    ✓ Iftar                   │
               │   │                                                     │
               │   │ [Update Participation]                              │
               │   └─────────────────────────────────────────────────────┘
               │
               ├─> Clicks "Update Participation"
               │
               └─> PARTICIPATION UPDATE MODAL
                   ┌─────────────────────────────────────────┐
                   │ Update Participation for: John Doe      │
                   │                                         │
                   │ Date: Thursday, February 6, 2026        │
                   │                                         │
                   │ □ Lunch                                 │
                   │ □ Snacks                                │
                   │ □ Iftar                                 │
                   │    ├─> Applicable  if enabled           │
                   │        by admin config                  │
                   │ □ Event Dinner                          │
                   │ □ Optional Dinner                       │
                   │                                         │
                   │ [Cancel]  [Update All to Opted-Out]     │
                   └─────────────────────────────────────────┘
                   │
                   ├─> Team Lead clicks "Update All to Opted-Out"
                   │
                   ├─> [API Calls: POST /api/meals/participation/admin]
                   │   Multiple requests (one per meal type):
                   │
                   ├─> [System updates all records]
                   │   - Sets is_participating = false for all meals
                   │   - Records updated_by = teamlead@company.com
                   │   - Records timestamp
                   │
                   └─> Success message:
                       "Participation updated for John Doe"
                       │
                       └─> Team Lead closes modal
                           │
                           └─> Headcount automatically updated

Total time: ~1-2 minutes 
```

Flow 3: Admin Viewing Headcount for Meal Planning

```
┌─────────────────────────────────────────────────────────────┐
│             Admin Daily Headcount Workflow                   │
└─────────────────────────────────────────────────────────────┘

Scenario: Logistics team needs headcount for meal preparation

1. Evening (9:00 PM) - Initial count for the day after (After cut-off time)
   │
   └─> Admin opens MHP application
       │
       └─> LOGIN as Admin
           │
           └─> ADMIN DASHBOARD
               │
               ├─> Automatically shows: "Today's Headcount Summary"
               │   ┌─────────────────────────────────────────────────┐
               │   │ Thursday, February 6, 2026                      │
               │   │                                                 │
               │   │ Total Employees: 100                            │
               │   │                                                 │
               │   │ ┌─────────────────┬──────────┬─────────────┐    │
               │   │ │ Meal Type       │ Count    │ Percentage  │    │
               │   │ ├─────────────────┼──────────┼─────────────┤    │
               │   │ │ Lunch           │    87    │    87%      │    │
               │   │ │ Snacks          │    92    │    92%      │    │
               │   │ │ Iftar           │    45    │    45%      │    │
               │   │ │ Event Dinner    │     0    │     0%      │    │
               │   │ │ Optional Dinner │    12    │    12%      │    │
               │   │ └─────────────────┴──────────┴─────────────┘    │
               │   │                                                 │
               │   │ Last Updated: 9:00 PM                           │
               │   │ [Export]                                        │
               │   └─────────────────────────────────────────────────┘
               │
               ├─> Admin notes numbers:
               │   - Lunch: 87 people
               │   - Snacks: 92 people
               │
               └─> Communicates to kitchen staff:
                   "Prepare lunch for 90 people (with buffer)"

Total time: ~20 seconds per check 
(vs. 10-15 minutes with Excel)
```

Flow 4: New Employee Registration

```
┌─────────────────────────────────────────────────────────────┐
│              New Employee Self-Registration                  │
└─────────────────────────────────────────────────────────────┘

1. New employee receives welcome email
   │
   ├─> Email contains: MHP application URL
   │
   └─> Opens URL in browser
       │
       └─> LANDING PAGE
           │
           ├─> Sees: "Login" and "Register" buttons
           │
           └─> Clicks "Register"
               │
               └─> REGISTRATION PAGE
                   ┌─────────────────────────────────────┐
                   │ Create Your Account                 │
                   │                                     │
                   │ Full Name: [               ]        │
                   │ Email:     [               ]        │
                   │ Password:  [               ]        │
                   │ Confirm:   [               ]        │
                   │ Teams:     [               ]        │
                   │                                     │
                   │ [Cancel]  [Register]                │
                   └─────────────────────────────────────┘
                   │
                   ├─> Fills in details:
                   │   - Name: "Alice Johnson"
                   │   - Email: "alice.johnson@company.com"
                   │   - Password: "SecurePass123!"
                   │   - team: "Marketing"
                   │
                   ├─> Clicks "Register"
                   │
                   ├─> [Frontend Validation]
                   │
                   ├─> [API Call: POST /api/users/register]
                   │   Request: {
                   │     name: "Alice Johnson",
                   │     email: "alice.johnson@company.com",
                   │     password: "SecurePass123!",
                   │     team: "Marketing"
                   │   }
                   │
                   ├─> [Backend Processing]
                   │
                   ├─> [Response: 201 Created]
                   │
                   └─> Success page:
                       "Account created successfully!"
                       │
                       └─> Auto-redirect to login page
                           │
                           └─> Employee logs in with new credentials
                               │
                               └─> Sees employee dashboard with today's meals

Alternative Flow 4A: Email Already Registered
   │
   ├─> Registration fails
   └─> Error: "An account with this email already exists"
       │
       └─> User can click "Login" instead

Total time: ~2 minutes 
```

Flow 5: Team Lead Viewing Team Participation
```
┌─────────────────────────────────────────────────────────────┐
│           Team Lead Viewing Team Participation              │
└─────────────────────────────────────────────────────────────┘

Scenario: Team Lead wants to see today's participation for their team

1. Team Lead logs in
   │
   └─> TEAM LEAD DASHBOARD
       │
       ├─> Views: "My Team - Today's Participation"
       │   ┌─────────────────────────────────────────────────────────┐
       │   │ Engineering Team - Thursday, February 19, 2026          │
       │   │                                                         │
       │   │ ┌────────────────┬────────┬────────┬────────┬──────┐    │
       │   │ │ Employee       │ Lunch  │ Snacks │ Iftar  │ Loc  │    │
       │   │ ├────────────────┼────────┼────────┼────────┼──────┤    │
       │   │ │ John Doe       │  ✓ In  │  ✓ In  │  ✓ In  │ Off  │    │
       │   │ │ Jane Smith     │  ✗ Out │  ✓ In  │  ✓ In  │ WFH  │    │
       │   │ │ Bob Wilson     │  ✓ In  │  ✓ In  │  ✗ Out │ Off  │    │
       │   │ └────────────────┴────────┴────────┴────────┴──────┘    │
       │   │                                                         │
       │   │ Team Summary: Lunch: 2/3 | Snacks: 3/3 | Iftar: 2/3     │
       │   │ Location: Office: 2 | WFH: 1                            │
       │   └─────────────────────────────────────────────────────────┘
       │
       └─> Total time: ~10 seconds

```

Flow 6: Admin Marking a Special Day
```
┌─────────────────────────────────────────────────────────────┐
│               Admin Marking a Special Day                   │
└─────────────────────────────────────────────────────────────┘

Scenario: Admin marks a date as a Government Holiday

1. Admin logs in
   │
   └─> ADMIN DASHBOARD
       │
       ├─> Navigates to "Special Day Controls"
       │
       └─> SPECIAL DAY FORM
           ┌─────────────────────────────────────────┐
           │ Mark Special Day                        │
           │                                         │
           │ Date:     [February 21, 2026   ]        │
           │ Type:     [Government Holiday ▼]        │
           │ Note:     [Shaheed Day          ]       │
           │                                         │
           │ [Cancel]  [Save]                        │
           └─────────────────────────────────────────┘
           │
           ├─> Admin clicks "Save"
           │
           ├─> [API Call: POST /api/special-days]
           │
           ├─> [System creates special day record]
           │   - Meal participation disabled for that date
           │   - All users see "Government Holiday" banner
           │
           └─> Success: "February 21 marked as Government Holiday"

Total time: ~30 seconds
```

Flow 7: Admin/Team Lead Applying Bulk Opt-Out
```
┌─────────────────────────────────────────────────────────────┐
│            Bulk Opt-Out for Team/Group                       │
└─────────────────────────────────────────────────────────────┘

Scenario: Marketing team is on an offsite, Team Lead marks all as opted out

1. Team Lead logs in
   │
   └─> TEAM LEAD DASHBOARD
       │
       ├─> Clicks "Bulk Actions"
       │
       └─> BULK ACTION FORM
           ┌─────────────────────────────────────────┐
           │ Bulk Update - Marketing Team            │
           │                                         │
           │ Date: [February 20, 2026      ]         │
           │ Action: [Opt Out All Meals    ▼]        │
           │                                         │
           │ Affected Members:                       │
           │   ☑ Alice Johnson                       │
           │   ☑ Charlie Brown                       │
           │   ☑ Diana Prince                        │
           │                                         │
           │ Reason: [Team offsite event   ]         │
           │                                         │
           │ [Cancel]  [Apply Bulk Action]            │
           └─────────────────────────────────────────┘
           │
           ├─> Team Lead clicks "Apply Bulk Action"
           │
           ├─> [API Call: POST /api/meals/participation/bulk]
           │
           ├─> [System updates all selected members]
           │   - Sets is_participating = false for all meals
           │   - Records updated_by = teamlead@company.com
           │   - Records timestamp for audit
           │
           └─> Success: "3 members opted out for February 20"

Total time: ~1 minute
```

Flow 8: Employee Setting Work Location
```
┌─────────────────────────────────────────────────────────────┐
│            Employee Setting Work Location                    │
└─────────────────────────────────────────────────────────────┘

Scenario: Employee marks their location as WFH for tomorrow

1. Employee logs in
   │
   └─> EMPLOYEE DASHBOARD
       │
       ├─> Sees "Work Location" section:
       │   ┌─────────────────────────────────────────┐
       │   │ Work Location                           │
       │   │                                         │
       │   │ Date: [February 20, 2026      ]         │
       │   │                                         │
       │   │ Location: ( ) Office   (●) WFH          │
       │   │                                         │
       │   │ [Save Location]                         │
       │   └─────────────────────────────────────────┘
       │
       ├─> Selects "WFH" and clicks "Save Location"
       │
       ├─> [API Call: PUT /api/work-locations]
       │
       ├─> [System records work location]
       │
       └─> Success: "Work location set to WFH for February 20"

Total time: ~15 seconds
```

Flow 9: Admin Generating Daily Announcement
```
┌─────────────────────────────────────────────────────────────┐
│          Admin Generating Daily Announcement                │
└─────────────────────────────────────────────────────────────┘

Scenario: Logistics generates a daily summary message

1. Admin logs in
   │
   └─> ADMIN DASHBOARD
       │
       ├─> Navigates to "Daily Announcement"
       │
       ├─> Selects date: February 20, 2026
       │
       ├─> Clicks "Generate Announcement"
       │
       ├─> [API Call: GET /api/announcements/draft?date=2026-02-20]
       │
       └─> GENERATED MESSAGE:
           ┌─────────────────────────────────────────────────────┐
           │ 📋 Meal Headcount - February 20, 2026               │
           │                                                     │
           │ 🏢 Special Note: Normal working day                 │
           │                                                     │
           │ Lunch:           85 people                          │
           │ Snacks:          90 people                          │
           │ Iftar:           42 people                          │
           │ Event Dinner:     0 people                          │
           │ Optional Dinner: 10 people                          │
           │                                                     │
           │ Office: 72 | WFH: 28                                │
           │                                                     │
           │ [Copy to Clipboard]                                 │
           └─────────────────────────────────────────────────────┘
           │
           └─> Admin clicks "Copy to Clipboard"
               │
               └─> Pastes into messaging platform

Total time: ~20 seconds
```

Flow 10: Admin Declaring Company-Wide WFH Period
```
┌─────────────────────────────────────────────────────────────┐
│         Admin Declaring Company-Wide WFH Period             │
└─────────────────────────────────────────────────────────────┘

Scenario: Company declares WFH for a week due to office renovation

1. Admin logs in
   │
   └─> ADMIN DASHBOARD
       │
       ├─> Navigates to "Company WFH Settings"
       │
       └─> WFH PERIOD FORM
           ┌─────────────────────────────────────────┐
           │ Declare Company-Wide WFH Period         │
           │                                         │
           │ Start Date: [March 1, 2026     ]        │
           │ End Date:   [March 7, 2026     ]        │
           │                                         │
           │ [Cancel]  [Declare WFH Period]          │
           └─────────────────────────────────────────┘
           │
           ├─> Admin clicks "Declare WFH Period"
           │
           ├─> [API Call: POST /api/wfh-periods]
           │
           ├─> [System creates WFH period record]
           │   - All employees treated as WFH for March 1-7
           │   - Individuals can still override to "Office"
           │   - Headcount reports reflect WFH default
           │
           └─> Success: "WFH period declared: March 1 - March 7, 2026"

Total time: ~30 seconds
```

### 4. Authentication and Authorization

```
● Build the login system in auth.py, using password hashing with passlib(bcrypt). JWT
token generation with python-jose, and token verification dependency.
● Implement {get_current_user()} dependency and create role-based permission
dependencies:
{require_employee(); require_team_lead(); require_admin()}.
● Implement FastAPI {Depends()} decorator to protect routes.
```
### 5. Backend API Development

Create routers in routers/ directory:
```
● auth.py - Authentication endpoints
● meals.py - Meal participation endpoints
● users.py - User management endpoints
● teams.py - Team visibility endpoints
● special_days.py - Special day control endpoints
● work_locations.py - Work location endpoints
● announcements.py - Daily announcement draft endpoints
```

Core endpoints:
```
● POST /api/auth/login - User authentication (returns JWT)
● POST /api/users/register - Self-registration
● GET /api/meals/today - Fetch today's meal types and user's participation status
● PUT /api/meals/participation - Employee opts in/out of meals
● POST /api/meals/participation/admin - Team Lead/Admin updates on
behalf of employee
● GET /api/users/{user_id} - View user details (Team Lead endpoint)
```

Admin Endpoints:
```
● POST /api/users/create - Create user with role
● GET /api/users - List all users
● PUT /api/users/{user_id} - Update user
● DELETE /api/users/{users_id) - Deactiveate user
```

```
● GET /api/meals/headcount/today - Get meal headcount totals
(Admin/Logistics only)
● GET /api/users/me - Current user profile
```

Team Visibility:
```
● GET /api/teams/me/participation - Team Lead views own team's participation for today
● GET /api/teams/all/participation - Admin views participation across all teams
● GET /api/teams - List all teams
```

Bulk Actions:
```
● POST /api/meals/participation/bulk - Bulk opt-out for a group of users (Team Lead: own team, Admin: any)
```

Special Day Controls:
```
● POST /api/special-days - Admin marks a date as Office Closed / Government Holiday / Special Celebration
● GET /api/special-days?date={date} - Get special day info for a date
● GET /api/special-days?start={date}&end={date} - List special days in a date range
● DELETE /api/special-days/{id} - Admin removes a special day entry
```

Improved Headcount:
```
● GET /api/meals/headcount?date={date} - Headcount totals by meal type, team, overall, and Office/WFH split
```

Work Location:
```
● PUT /api/work-locations - Employee sets their work location for a date
● GET /api/work-locations?user_id={id}&date={date} - Get work location for a user/date
● PUT /api/work-locations/admin - Team Lead/Admin corrects a missing work-location entry
```

Company-Wide WFH:
```
● POST /api/wfh-periods - Admin declares a date range as WFH for everyone
● GET /api/wfh-periods - List all declared WFH periods
● DELETE /api/wfh-periods/{id} - Admin removes a WFH period
```

Daily Announcement:
```
● GET /api/announcements/draft?date={date} - Generate copy/paste-friendly announcement for a date
```
FastAPI features to be used:
```
● Automatic OpenAPI docs at /docs
● Request/response validation with Pydantic
● Dependency injection for auth
● CORS middleware configuration
```

## Implementation Priority

### Phase 1 (Core MVP)
1. POST /api/auth/login
2. POST /api/users/register
3. GET /api/users/me
4. GET /api/meals/today
5. PUT /api/meals/participation
6. GET /api/meals/headcount/today

### Phase 2 (Admin Features)
7. POST /api/users/create
8. POST /api/meals/participation/admin
9. GET /api/users
10. GET /api/users/{user_id}

### Phase 3 (Management)
11. PUT /api/users/{user_id}
12. DELETE /api/users/{user_id}

### Phase 4 (Team & Location)
13. GET /api/teams/me/participation
14. GET /api/teams/all/participation
15. PUT /api/work-locations
16. PUT /api/work-locations/admin
17. GET /api/work-locations

### Phase 5 (Special Days & Bulk)
18. POST /api/special-days
19. GET /api/special-days
20. DELETE /api/special-days/{id}
21. POST /api/meals/participation/bulk

### Phase 6 (Reporting & Announcements)
22. GET /api/meals/headcount (improved with team/location splits)
23. GET /api/announcements/draft
24. POST /api/wfh-periods
25. GET /api/wfh-periods
26. DELETE /api/wfh-periods/{id}

### 6. Frontend Development

Initialize a React app with Vite and install dependencies using react-router-dom, axios. Create
API service layer in services/api.js. Set up the auth context for global user state.
Pages/Views:
```
● LoginPage.jsx - Login form
● EmployeeDashboard.jsx
○ Today's date display
○ List of meals with opt-in/out toggles
○ Confirmation feedback on updates
○ Team name display
○ Work location selector for a date
○ Special day banner (holiday/office closed/celebration)
● AdminDashboard.jsx
○ Headcount summary view (totals per meal type, per team, Office/WFH split)
○ Option to update employee participation
○ Employee search/filter functionality
○ Special day controls panel
○ Daily announcement generator
○ Company-wide WFH period management
● TeamLeadDashboard.jsx
○ Team participation overview for the day
○ Bulk action controls (opt-out group of team members)
○ Correct missing work-location entries for team members
```
Components:

1. PrivateRoute.jsx - Protected route wrapper
2. MealCard.jsx - Individual meal participation toggle
3. HeadcountTable.jsx - Summary table for admin (with team/location breakdowns)
4. Navbar.jsx - Navigation with user role indicator
5. Loading.jsx, ErrorMessage.jsx - UI states
6. TeamParticipationView.jsx - Team-level participation grid
7. SpecialDayBanner.jsx - Displays special day status for the selected date
8. SpecialDayForm.jsx - Admin form to mark a day as holiday/closed/celebration
9. BulkActionForm.jsx - Bulk opt-out form for Team Lead/Admin
10. WorkLocationSelector.jsx - Employee work location picker (Office / WFH)
11. AnnouncementDraft.jsx - Generates and displays copy/paste-friendly announcement
12. WFHPeriodManager.jsx - Admin form to declare/manage company-wide WFH periods
13. LiveHeadcount.jsx - Real-time headcount display that updates without reload
Implement auth context for user session and token for state management. Local state for meal
participation data and API calls wrapped in try-catch with loading states.
Implement polling or WebSocket-based mechanism for live headcount updates (FR-11).


### 7. Other Logic Implementation

Default all employees to “opted-in” for all meals, while also allowing employees to toggle
participation status. Prevent duplicate entries for the same user/date/meal. Calculate real-time
headcount aggregations, and validate role permissions for admin actions.

### 8. Documentation, Testing and Validation

Test authentication flow for all roles and feature verifications.

**Testing Pyramid:**
```
         /\
        /  \
       / E2E \           10% - End-to-End Tests
      /______\
     /        \
    / Integr.  \        30% - Integration Tests
   /____________\
  /              \
 /   Unit Tests   \     60% - Unit Tests
/__________________\
```


- Verify employee can opt-in/out correctly
```
- All verification related to meal participation and headcount must respect the 9:00 PM snapshot rule
- The system generates a single authoritative headcount snapshot at 9:00 PM
  for the next day
- This snapshot is what gets notified to the logistics team
- Any employee opt-in / opt-out after 9:00 PM:
  - Is not included in the notification already sent
  - Is disabled until count start for next snapshot
- Admin dashboard updates are pull-based and do not trigger notifications
```
- Verify admin can update on behalf of employees
- Test headcount calculations accuracy
Add a README with setup instructions and API documentation (endpoints, payloads,
responses). Add an user guide for each role with a sample .env configuration.

### 9. Local Deployment/Operations

**Deployment Strategy:**

**Development Environment:**
- Backend: Use uvicorn with port 8000
- Frontend: `npm run dev` (Vite dev server on port 5173)

**Monitoring Strategy:**
- Application logs to file and console
- Health check endpoint at /health
- Authentication attempt logging
- Update attempt logging (including cutoff violations)

**Backup Strategy:**
- Daily automated JSON file backups
- 30-day retention policy
- Manual backup before major updates

#### Common Issues 

**Issue 1: Backend won't start**
```
Error: Port 8000 already in use

Solution:
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>
```

**Issue 2: Frontend can't connect to backend**
```
Error: CORS error / Network error

Solution:
1. Verify backend is running (http://localhost:8000/docs)
2. Check VITE_API_URL in frontend/.env
3. Verify CORS configuration in backend/app/main.py
```

**Issue 3: JSON file corrupted**
```
Error: JSONDecodeError

Solution:
1. Stop application
2. Restore from latest backup
3. Investigate cause (concurrent writes, system crash)
4. Implement file locking if needed
```

**Issue 4: Token expired**
```
Error: 401 Unauthorized

Solution:
This is expected behavior (30 min expiration)
User should log in again
```
---
## Risks, Assumptions, and Open Questions

### Risks
#### High Priority Risks

**Risk 1: Data Loss Due to File Corruption**
- **Likelihood:** Medium
- **Impact:** High
- **Mitigation:**
  - Implement atomic file writes
  - Daily automated backups
- **Contingency:** Restore from latest backup (max 1 day data loss)

**Risk 2: Concurrent Write Conflicts**
- **Likelihood:** Medium (100+ users)
- **Impact:** Medium (data inconsistency)
- **Mitigation:**
  - Implement file locking mechanism
  - User feedback on conflicts
- **Contingency:** Manual data correction by admin

**Risk 3: Low User Adoption**
- **Likelihood:** Low
- **Impact:** High (project failure)
- **Mitigation:**
  - Simple, intuitive UI design
  - Training session before launch
- **Contingency:** Iterate on UI based on feedback

**Risk 4: Performance Degradation with Scale**
- **Likelihood:** Low (for 100 users)
- **Impact:** Medium
- **Mitigation:**
  - Performance testing before launch
- **Contingency:** Accelerate database migration

#### Medium Priority Risks

**Risk 5: Security Breach**
- **Likelihood:** Low
- **Impact:** High
- **Mitigation:**
  - bcrypt password hashing
  - JWT token security
  - Input validation
- **Contingency:** Password reset for all users

**Risk 6: Browser Compatibility Issues**
- **Likelihood:** Low
- **Impact:** Low
- **Mitigation:**
  - Test on Chrome, Firefox, Edge
  - Use standard web APIs
- **Contingency:** Document supported browsers

**Risk 7: Developer Availability**
- **Likelihood:** Medium
- **Impact:** Medium
- **Mitigation:**
  - Good documentation
  - Simple architecture
- **Contingency:** Knowledge transfer session

**Risk 8: Live Update Performance**
- **Likelihood:** Medium
- **Impact:** Medium (poor UX if polling is too frequent or too slow)
- **Mitigation:**
  - Use reasonable polling interval (15 seconds)
  - Optimize headcount aggregation queries
- **Contingency:** Increase polling interval or defer to WebSocket in future iteration

**Risk 9: Special Day Misconfiguration**
- **Likelihood:** Low
- **Impact:** Medium (meals disabled on wrong day)
- **Mitigation:**
  - Confirmation prompt before saving special day
  - Allow Admin to delete/correct special day entries
- **Contingency:** Admin can remove the incorrect entry immediately

### Assumptions

#### Technical Assumptions

1. **All employees have computer access** during work hours
2. **Company network is reliable** (99%+ uptime during business hours)
3. **JSON files sufficient for 6 months** before database migration needed

#### Business Assumptions

4. **Employees will check system daily** (not rely on notifications)
5. **Current meal types will not change frequently**
6. **Default opt-in acceptable** to stakeholders and employees
7. **30-minute token expiration acceptable** for security/UX balance
8. **Teams are pre-defined and stable** — team assignments do not change frequently
9. **Work location is typically known a day in advance** by employees
10. **Company-wide WFH periods are rare events** declared by Admin

#### Process Assumptions

11. **Admins available during business hours** for support
12. **Logistics team checks headcount 2-3 times per day** (not real-time requirement)
13. **Same-day updates sufficient** (no advance planning needed)
14. **Logistics team uses the daily announcement draft** to communicate with kitchen staff
15. **Special days (holidays/closures) are known in advance** and set by Admin before the date

---

## Key Design Decisions

1. **Default opt-in approach** - All employees assumed participating unless they opt out
2. **Same-day focus** - Only "today's" meals visible and editable (no historical/future view
    yet)
3. **Simple storage** - File-based JSON (easy to migrate to DB later)
4. **Minimal validation** - Basic role checks; advanced cutoff logic deferred to later iterations
5. **Real-time counts** - Headcount calculated on-demand from participation records
6. **Team-scoped access** - Team Leads see and manage only their own team's data; Admins see all
7. **Special day overrides meals** - Office Closed and Government Holiday disable meal participation for the date
8. **WFH default with override** - Company-wide WFH periods set default location; individuals can override to Office
9. **Polling for live updates** - Use short-interval polling (e.g., 15s) rather than WebSockets for simplicity
10. **Announcement as text** - Daily announcement is plain text for copy/paste, not email integration
11. **Date-based work location** - Work location is tracked per user per date, not as a permanent attribute
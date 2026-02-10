# First iteration of Meal Headcount Planner

# (MHP)

```
Niloy Gabriel Gomes
Feb 6, 2026
Status: Draft - Pending Review
```

- [Overview](#overview)
   - Tech Stack
   - Summary
   - Problem Statement
- [Goals and Non-Goals](#goals-and-non-goals)
   - Goals (Iteration 1)
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
- [Key Design Decisions for Iteration](#key-design-decisions-for-iteration)

---

## Overview

Build a web app to track daily meal participation for 100+ employees, replacing Excel-based
tracking.

### Tech Stack

```
Frontend: React + Vite
Backend API: Python (FastAPI)
Authentication: Basic login with roles (Employee / Team Lead / Admin/Logistics)
Storage: File-based JSON for the first iteration
Packaging: Run locally
Development Tools:
● Backend: pip + requirements.txt
● Frontend: npm or pnpm
● CORS middleware enabled for local development
```
### Summary

```
This document contains a comprehensive, development roadmap for building the first
iteration of the Meal Headcount Planner (MHP). It outlines the complete technical
implementation using Python-FastAPI for the backend and React for the frontend,
including detailed guidance on project structure, data models, authentication, API,
endpoints, and UI components. The plan breaks down the development process into
actionable phases, from initial setup through local deployment, with specific
implementation details for each layer of the stack. Additionally, it includes key design
decisions, success criteria, and clearly defines what features are in-scope versus deferred
to future iterations.
```
### Problem Statement
The organization currently uses a manual Excel-based process to track daily meal participation for 100+ employees. This approach presents several critical challenges, like operational ineffeciencies, data quality issues, and potential negative business impacts due to inaccurate head counts. The proposed solution targets to alleviate these challenges by increasing efficiency and accuracy.

---

## Goals and Non-Goals

### Goals (Iteration 1)

**Primary Goals:**

1. **Enable Self-Service Meal Management**
2. **Provide Real-Time Headcount Visibility**
3. **Implement Role-Based Access Control**
4. **Replace Excel with Reliable System**
5. **Default Opt-In Approach**

**Secondary Goals:**

6. **Build Foundation for Future Iterations**
   - Design architecture to support database migration
   - Create extensible data models
   - Implement authentication framework for future features

7. **Provide Audit Trail**
   - Track who made changes to participation records
   - Record timestamps for all updates
   - Enable troubleshooting and accountability

### Non-Goals

**Features Deferred to Future Iterations:**

1. **Advanced Planning Features**
   - Multi-day meal planning (only "today" in Iteration 1)
   - Weekly/monthly calendar view
   - Advance meal scheduling
   - Recurring participation patterns

2. **Cutoff Time Enforcement**
3. **Special Day Handling**
4. **Notifications and Reminders**
5. **Analytics and Reporting**
6. **Advanced User Management**  

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
          │  │   └─ users.py            │  │                 
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
          │  └─ get_headcount_by_date()    │                 
          └───────────────┬────────────────┘                 
                          │                                   
                    JSON File I/O                             
                          │                                   
          ┌───────────────▼────────────────┐                 
          │   File System                  │                
          │                                │                 
          │  /backend/data/                │                 
          │  ├─ users.json                 │                 
          │  └─ meal_participation.json    │                 
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
│ │ └── meal_participation.json
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
Implement file-based JSON storage utilities in storage.py. Use {load_json(filename)} to
read data, {save_json(filename, data)} to write data, and {get_by_id();
create(); update(); delete()} as helpers. Create seed data for testing purposes.

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
                   │   │    ├─> Applicable  if enabled   │ ← Changed
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
                   │   │       │ ✗ Lunch         [Opted Out]    │  ← Changed
                   │   │       │ ✓ Snacks        [Opted In ]    │
                   │   │       │ ✓ Iftar         [Opted In ]    │
                   │   │       │   ├─> Applicable  if enabled   │ ← Changed
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
                   │    ├─> Applicable  if enabled           │ ← Changed
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

Scenario: Logistics team needs headcount for meal preparation ← Changed

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
                   │ Teams:     [               ]        │ ← Changed
                   │                                     │
                   │ [Cancel]  [Register]                │
                   └─────────────────────────────────────┘
                   │
                   ├─> Fills in details:
                   │   - Name: "Alice Johnson"
                   │   - Email: "alice.johnson@company.com"
                   │   - Password: "SecurePass123!"
                   │   - team: "Marketing"                 ← Changed
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
                   │     team: "Marketing"                ← Changed
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

### 6. Frontend Development

Initialize a React app with Vite and install dependencies using react-router-dom, axios. Create
API service layer in services/api.js. Set up the auth context for global user state.
Pages/Views:
● LoginPage.jsx - Login form
● EmployeeDashboard.jsx
○ Today's date display
○ List of meals with opt-in/out toggles
○ Confirmation feedback on updates
● AdminDashboard.jsx
○ Headcount summary view (totals per meal type)
○ Option to update employee participation
○ Employee search/filter functionality
Components:

1. PrivateRoute.jsx - Protected route wrapper
2. MealCard.jsx - Individual meal participation card/toggle
3. HeadcountTable.jsx - Summary table for admin
4. Navbar.jsx - Navigation with user role indicator
5. Loading.jsx, ErrorMessage.jsx - UI states
Implement auth context for user session and token for state management. Local state for meal
participation data and API calls wrapped in try-catch with loading states.


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
  - Is reflected in the admin dashboard
  - Is not included in the notification already sent
- Admin dashboard updates are pull-based and do not trigger notifications
```
- Verify admin can update on behalf of employees
- Test headcount calculations accuracy
Add a README with setup instructions and API documentation (endpoints, payloads,
responses). Add an user guide for each role with a sample .env configuration.

### 9. Local Deployment/Operations ← Changed

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

### Assumptions

#### Technical Assumptions

1. **All employees have computer access** during work hours
2. **Company network is reliable** (99%+ uptime during business hours)
3. **JSON files sufficient for 6 months** before database migration needed

#### Business Assumptions

4. **Employees will check system daily** (not rely on notifications)
5. **Current meal types will not change frequently** in Iteration 1
6. **Default opt-in acceptable** to stakeholders and employees
7. **30-minute token expiration acceptable** for security/UX balance

#### Process Assumptions

8. **Admins available during business hours** for support
9. **Logistics team checks headcount 2-3 times per day** (not real-time requirement)
10. **Same-day updates sufficient** (no advance planning needed in Iteration 1)

---

## Key Design Decisions for Iteration

1. **Default opt-in approach** - All employees assumed participating unless they opt out
2. **Same-day focus** - Only "today's" meals visible and editable (no historical/future view
    yet)
3. **Simple storage** - File-based JSON (easy to migrate to DB later)
4. **Minimal validation** - Basic role checks; advanced cutoff logic deferred to later iterations
5. **Real-time counts** - Headcount calculated on-demand from participation records




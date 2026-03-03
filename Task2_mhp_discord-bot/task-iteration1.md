# Project: Meal Headcount Planner (MHP) — Task 2 (Weeks 3–4)
Add a Discord bot as an input channel while evolving MHP into a production-grade system with DynamoDB persistence, a structured web dashboard, containerized runtime, and CI/CD.

## Iteration 1 (Week 1) — Discord Input + Web Dashboard Architecture (FE3 + FE4 + BE3)
### Feature requests
1. **Discord bot: employee self-update**
   - Employees can update their meal participation for a selected date.
   - Employees can update their work location (Office/WFH) for a selected date.
   - Bot replies with the user’s current status summary after each change.

2. **Discord bot: team/admin quick views**
   - Team Leads can request a team-level headcount summary for a selected date.
   - Admin/Logistics can request overall headcount summary for a selected date.

3. **Web dashboard: component-based UI**
   - Admin/Logistics dashboard displays meal totals, Office vs WFH split, and special-day indicators.
   - Team Lead view displays team participation list and rollups.
   - UI is clearly organized into reusable components (filters, summary cards, employee list, day banner).

4. **Web dashboard: shared state + live updates**
   - Dashboard supports changing selected date and filters (team, meal type, WFH).
   - Totals and rollups update immediately as filters or entries change.

5. **Compute paradigm: async summary generation**
   - When Admin triggers “Generate daily summary”, the system processes it asynchronously.
   - UI/bot shows “in progress” → “ready” status.

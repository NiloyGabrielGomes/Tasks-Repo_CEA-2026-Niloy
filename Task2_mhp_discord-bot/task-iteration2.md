## Iteration 2 (Week 2) — DynamoDB + Scheduled Summaries + Docker + CI/CD (BE4 + DO1 + DO2 + BE3)
### Feature requests
1. **DynamoDB persistence**
   - Persist participation entries, work-location entries, special days, and company-wide WFH periods.
   - Reports and dashboards read from persisted data.

2. **Report-ready retrieval**
   - Admin can retrieve daily totals quickly for a selected date.
   - Team Leads can retrieve team-level participation quickly for a selected date.
   - Monthly WFH usage summary is available (soft limit: accept beyond 5, but flag/report it).

3. **Scheduled daily post to Discord**
   - System posts a daily summary message to a configured Discord channel at a configured time.
   - The post includes meal totals and special-day context (holiday/office closed/celebration).

4. **Containerized delivery**
   - System runs via containers (web + backend + bot).
   - A single “run locally” workflow exists for developers.

5. **CI/CD pipeline** (deferred to later and not done yet)
   - On pull requests: run checks and build artifacts.
   - On merge to main: publish release artifacts (and optionally deploy to a shared internal environment).
   - Build version is visible in the web UI and included in bot responses (basic release visibility).

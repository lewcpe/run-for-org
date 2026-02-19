Run for Organization
====

Backend for Virtual Run Event for an organization

- Allow user to login via Auth0 or Firebase, email/password. if same email (always lowercase) logged in via multiple channel, login into same account
- Use sqlite, alembic, sqlalchemy, fastapi
- the application has config for start_date, end_date , total_step_goal
- record running log for each user. each log entry consist of running_datetime, step_count, range, created_at, owner_id
- user could record step by range or step_count or both, but if user input just one thing, compute another by env RUNORG_STEP_PER_KM (default=1500). make STEP_PER_KM available to frontend via config PAPI
- backend url in /api
- APIs make following data available
  - overall organization show progress: percentage of total_stepgoal
  - total step count by week
  - leaderboard of top users (limit to env RUNORG_TOP_USER, default=5) with total step count for each user
  - user's total step count
  - user's step count by week
  - user's running record (paginated)
- user could modify or edit his own records
- all create, update, delete of users and running record will be logged in logs table with field (user_id, message, time). all logs are append only
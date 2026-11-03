# HELPNET Selenium Test Plan

## Purpose and scope

Run the existing pytest/Selenium suite against HELPNET's Django application
before preparing project reports. The suite covers authentication, profile
management, NGO verification, ratings, blood donation, volunteering, goods,
health, farming, waste collection, and rendered-page routes.

## Environment and command

The browser tests use the repository's existing `.venv`, Django `live_server`,
SQLite test database, Selenium WebDriver, and Chrome. No separate frontend
server or npm build is configured.

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\selenium -q
```

For browser cases only, excluding the HTTP-only rendered-page route checks:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\selenium -q -k "not declared_page_get_routes"
```

## Recent feature cases

1. Create multiple personal profiles for one account; switch profiles; edit
   profile details; deactivate and reactivate a profile; ensure the account
   remains present.
2. Create an NGO profile; enter organization information; reject invalid type
   and oversized files; accept the required registration certificate and
   optional supporting file; verify pending status and private document access.
3. Use an administrator account to approve, reject, and request additional
   documents; verify review reason, timestamps, status, and admin document
   access.
4. Verify Bangla/English labels and dynamic profile content, language
   persistence after refresh, ratings, gender/role text, and farmer listing
   titles.
5. Edit and save the user's profile details from the profile page.

## Existing regression coverage

The existing suite covers account registration/login and validation,
authentication gates, identity verification submission, donor availability
and blood requests, ratings and notifications, volunteer signup and
coordination, goods listings and conversations, health questions and
professional listings, waste pickup and ratings, farmer listings and privacy,
and protected pages. API/backend tests provide additional coverage for private
document authorization, NGO replacement flows, profile permissions, and
review transitions.

## Evidence and result recording

Each Selenium browser case writes a screenshot to
`project_documentation/selenium_evidence/`. HTTP-only route checks have no
browser screenshot and are marked as such in the CSV. Test IDs, preconditions,
steps, outcomes, and screenshot references are recorded in
[`selenium_test_cases.md`](../../project_documentation/selenium_evidence/selenium_test_cases.md),
[`selenium_execution_report.md`](../../project_documentation/selenium_evidence/selenium_execution_report.md),
and
[`selenium_test_results.csv`](../../project_documentation/selenium_evidence/selenium_test_results.csv).

## Limitations

Tests use generated test accounts and synthetic records on the local test
database, not production user data. Some authenticated tests seed a test JWT
in browser storage rather than navigating the login form. Production MySQL,
SMTP, deployed media storage, load, and accessibility testing are outside this
suite. Do not treat these results as deployment certification.

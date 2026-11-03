# HELPNET Final Audit Report

**Audit date:** 2026-11-03  
**Branch/commit audited:** `samia` / `e1523e3`  
**Overall result:** Backend and browser regression suites pass in the local
test environment. Production MySQL/deployment validation remains outstanding.

## Summary

The repository contains Django APIs and template/JavaScript workflows for
accounts and profiles, volunteering, ratings, blood donation, notifications,
NGO approval, identity verification, goods, health, farming, waste, reports,
and administration. Selenium exercised 51 browser workflows against Django's
live test server and test database; 47 additional page-route checks used HTTP
requests. These are local automated tests, not a production deployment test.
The generated project documents and execution evidence are under
`project_documentation/`.

## Bugs fixed

1. Private uploads were removed from the current Git index and excluded by
   `.gitignore`, with all 19 local copies preserved.
2. Settings no longer hardcode a development key, enable DEBUG, or allow all
   CORS origins by default. Production requires a long secret and explicit
   hosts; HTTPS and secure cookies default on with DEBUG off.
3. Verification admin dynamic HTML rendering was replaced with safe DOM text.
4. Health-professional review JavaScript is loaded on the correct admin page
   using Django's static path.
5. Generic volunteer-certificate POST now validates `event_id` instead of
   failing due to a route/handler argument mismatch.
6. Blood request documents now use private storage and requester/superuser-only
   downloads, validated file signatures, and a migration for referenced legacy
   files.
7. Unrated-user summaries now return null rather than a fabricated 5.0 average.
8. Root README and project summary now contain setup and current audit guidance.
9. Dashboard profile controls now support editing and reactivating existing
   profiles; NGO profiles use pending/rejected approval messaging without
   conflating approval with personal identity verification.
10. Farmer owners/admins can edit existing produce fields, including restoring
    availability; targeted dashboard, NGO-approval, and farmer interfaces have
    Bangla/English text, and the volunteer-opportunity navigation button was
    restyled for consistent sizing and responsive layout.
11. Added private NGO verification documents, organization details, upload
    validation, owner/admin-only download access, status/reason/timestamps,
    admin review actions, and dashboard/admin-page forms. The account continues
    to support personal profiles under the same login; NGO approval remains
    separate from personal NID verification.

All changes are uncommitted. The current index includes staged removals for the
19 private upload assets; their working copies remain intact.

## Remaining issues and risks

- Previously committed private uploads and the old source-coded development key
  remain in Git history. History purge and any force-push require repository
  owner/team coordination; neither was performed.
- Production MySQL and the live data migrations remain unverified; only the
  SQLite test configuration was exercised for automated checks.
- HSTS remains opt-in pending confirmation of the deployment's HTTPS and
  subdomain policy.
- Blood donor `available` query behavior is undefined; the UI does not use it.
- Rating uniqueness remains per user pair rather than per interaction because
  no interaction model exists.
- `GoodsReport` exists but reporting uses generic `Report`.
- Health-professional eligibility still depends on the legacy Citizen role.
- Cloudinary is not configured; backups remain manual.
- Requirement traceability, teacher-provided sample styling, actual team
  contributions, budget, approvals, stakeholder evidence, and a recorded
  demonstration remain unverified. Selenium evidence screenshots are present.

## Modules verified

The 128-test backend suite passes for Blood, Common, Farmer, Goods, Health,
Notifications, Ratings, Reports, Users, Verification, Volunteer, and Waste.
The browser suite passed all 51 Selenium cases; the full Selenium-directory
run also passed 47 HTTP-only page-route checks after four fixture failures
were corrected and rerun.

## Test outcomes

- **PASS:** Django system check under test/SQLite settings.
- **PASS:** No migration drift.
- **PASS:** Python compilation and Git whitespace checks.
- **PASS:** 128 backend tests.
- **PASS:** 51 Selenium browser tests against Django's live test server; 51
  per-test screenshots were saved. The initial 98-case run had 94 passes and
  four NGO-profile fixture failures; all four affected cases passed when
  rerun after fixture correction.
- **PASS:** 47 HTTP-only rendered-page route checks in the 98-case Selenium
  directory run.
- **PASS:** Selenium-tested NGO submission, validation, private document
  access, admin review decisions, profile lifecycle, profile editing, and
  bilingual profile content.
- **NOT TESTED:** Production MySQL migration, SMTP delivery, live deployment,
  load/performance, and standalone JavaScript lint/build.
- **WARNING:** Simulated production `check --deploy` reports HSTS not configured.

## Submission readiness

The requested technical, academic, testing, API, database, and user documents
are generated under `project_documentation/`. No teacher-provided sample/SRS/
SDS or verified team-contribution, budget, approval, or stakeholder records
were available; those details are marked as limitations rather than invented.

See [Project Audit](PROJECT_AUDIT.md), [Bug Tracker](BUG_TRACKER.md),
[Test Report](TEST_REPORT.md), and [Security Report](SECURITY_REPORT.md).

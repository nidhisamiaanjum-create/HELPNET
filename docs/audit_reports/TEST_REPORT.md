# HELPNET Test Report

**Execution date:** 2026-11-03  
**Environment:** Windows; Python 3.14; Django 5.2; pytest; Chrome with Selenium.  
**Scope:** Current worktree; local SQLite test database and Django live test server.

## Result summary

| Test group | Result | Evidence |
|---|---|---|
| Backend automated suite | PASS | 128 passed, 0 failed. |
| Selenium browser workflows | PASS | 51 passed; 51 per-test screenshots saved under `project_documentation/selenium_evidence/`. |
| Rendered-page route checks | PASS | 47 HTTP-only page-route checks passed. These were not browser tests. |
| Django system check | PASS | No issues reported with the test/SQLite settings. |
| Migration drift check | PASS | `makemigrations --check --dry-run` reported no changes. |
| Whitespace check | PASS | `git diff --check` reported no errors. |
| Production MySQL/deployment | NOT TESTED | Test execution used SQLite and Django's local live test server. |
| Standalone JavaScript lint/build | NOT TESTED | No frontend lint/build command is configured in the project. |

## Selenium execution and fixes

The initial 98-case Selenium-directory run reported 94 passed and 4 failed.
Those four failures were existing opportunity/coordinator tests whose fixtures
set only the legacy NGO approval field; they did not make the NGO profile
active or set its canonical verification status. The fixtures were updated to
match the current permission rules, and all four affected cases passed when
rerun. The final unique-case outcomes were 98 passed and 0 outstanding
failures.

A separate final browser run executed all 51 cases that use Selenium WebDriver:

```text
51 passed, 47 deselected in 895.62s
```

The 47 deselected tests are HTTP-only rendered-page route checks, not Selenium
browser tests. The full directory run executed those route checks as part of
the 98 cases.

Selenium uncovered and verified fixes for two UI defects:

1. NGO invalid-file validation errors reached the frontend but were hidden by
   the `.field-error` styling. The dashboard now visibly presents the
   submission status and error feedback.
2. The profile editing form lacked a Save button, and JavaScript assumed
   optional privacy controls existed on the page. A localized Save button was
   added and optional privacy controls are now handled safely.

The additional seven-case suite exercises profile creation/switch/edit/
deactivation/reactivation; NGO form submission, required and optional files,
invalid type and size handling, private owner/admin access and outsider
denial; admin approval/rejection/additional-document decisions; bilingual
profile content and persistence; and profile-page editing.

## Backend test distribution

| App/test area | Passed |
|---|---:|
| Blood | 14 |
| Common/page rendering | 3 |
| Farmer | 11 |
| Goods | 10 |
| Health | 9 |
| Notifications | 5 |
| Ratings | 10 |
| Reports | 5 |
| Users: NGO verification, approval, permissions, profiles | 35 |
| Identity verification | 1 |
| Volunteer | 13 |
| Waste | 12 |
| **Total** | **128** |

## Test environment and limitations

Browser tests start Django's `live_server` and use a test database, generated
test users, and synthetic records. This exercises the real application code
and frontend/API requests; it does not use mocked API responses. Several
authenticated feature tests seed the test JWT into browser storage instead of
performing login through the form, so they are not all full login-to-feature
journeys. Registration/login workflows are separately covered by browser
tests.

Backend tests cover private blood-document authorization, NGO replacement and
additional-document transitions, personal NID separation, ownership rules,
and profile switching. The browser suite does not cover every administrative
page or every document-replacement scenario. No production MySQL migration,
SMTP delivery, deployed storage, load test, accessibility audit, or
standalone JavaScript lint/build was performed. HSTS remains opt-in pending
deployment HTTPS policy confirmation.

Detailed test IDs, cases, outcomes, and screenshot references are in
[`project_documentation/selenium_evidence/selenium_test_results.csv`](../project_documentation/selenium_evidence/selenium_test_results.csv)
and
[`project_documentation/selenium_evidence/selenium_execution_report.md`](../project_documentation/selenium_evidence/selenium_execution_report.md).

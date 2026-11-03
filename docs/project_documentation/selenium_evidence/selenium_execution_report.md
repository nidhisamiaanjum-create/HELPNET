# Selenium Execution Report

**Execution date:** 2026-11-03  
**Application:** HELPNET Django `live_server` and its SQLite test database.  
**Browser:** Headless Chrome through Selenium WebDriver.  
**Final outcomes:** 51 Selenium browser cases passed; 47 HTTP-only rendered-page checks passed; 98 unique cases passed after targeted reruns.

## Run history

| Run | Scope | Outcome |
|---|---|---|
| Initial full directory run | 98 cases | 94 passed, 4 failed. Failures were existing NGO coordinator fixtures that set only legacy approval. |
| Fixture correction and targeted rerun | 4 affected cases | 4 passed after setting an active NGO profile and canonical approved status. |
| Final browser screenshot run | 51 Selenium cases | 51 passed in 895.62 seconds; one final screenshot per browser case was saved. |
| HTTP route checks | 47 direct page GET cases | Passed in the full-directory run; these are not Selenium browser tests. |
| Backend suite | 128 tests | 128 passed in 28.34 seconds on the final rerun. |

## Browser coverage

Account registration/login and validation; profile editing and lifecycle; NGO submission, validation, and private files; approval/rejection/additional-document decisions; bilingual profile content; blood donor/request flows; ratings and notifications; volunteer signup/coordinator restrictions/messages/search; goods listings/interests; health questions and verified-professional listings; farmer listings/privacy; waste pickup and collector ratings; protected pages.

## Defects found and corrected

1. NGO invalid-file validation errors reached the frontend but were hidden by `.field-error` styling. Dashboard feedback visibility was fixed.
2. The profile page lacked a Save control and assumed optional privacy fields existed. A localized Save button and safe optional-control handling were added.
3. Four older volunteer/coordinator fixtures did not construct an active, canonically approved NGO profile. Fixtures now match current permission rules.

The UI cases and four fixture-dependent cases were rerun successfully. The seven feature-specific scenarios have passing screenshots in this folder.

## Authentication and evidence limitations

Tests use generated users and synthetic records in an isolated test database. Selenium exercises the real local frontend and server; API responses are not mocked. Some authenticated tests install a test JWT in local browser storage rather than navigating the login form, so they are not all complete login-to-feature journeys. No production account/data was used.

Screenshots are saved for all 51 Selenium browser cases. The 47 HTTP-only route cases are marked `N/A` because no browser session is created. The CSV records each unique case, preconditions, steps, expected/actual result, status, date, and screenshot evidence.

The evidence folder also retains `*-failed.png` files from earlier intermediate
runs. They document pre-fix or fixture failures and are not the final result;
the CSV references only the latest passing browser screenshots.

## Not covered by this browser run

- Production MySQL migration or deployed media storage.
- External SMTP/password-reset mail delivery.
- Production authentication/session configuration and real user data.
- Every admin verification and document-replacement scenario; backend/API coverage is identified separately.
- Load, performance, accessibility, and standalone JavaScript lint/build tests.

See [selenium_test_cases.md](selenium_test_cases.md) and [selenium_test_results.csv](selenium_test_results.csv).

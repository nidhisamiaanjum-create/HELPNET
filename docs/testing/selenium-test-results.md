# Selenium Test Results

**Status:** This file is the current results index for the 2026-11-03 local
test run. Detailed evidence is kept in `project_documentation/selenium_evidence/`.

| Group | Result |
|---|---|
| Selenium WebDriver browser tests | 51 passed; 51 screenshots saved |
| HTTP-only rendered-page route checks | 47 passed; these are not Selenium browser tests |
| Full Selenium-directory unique cases | 98 passed after four fixture failures were corrected and rerun |
| Backend automated tests | 128 passed |

The browser tests used Django's live test server, a test database, generated
test users, and synthetic records. Some authenticated tests seed test JWTs in
browser storage; the suite is not a production deployment test and does not
claim that every feature uses the login form.

See:

- [`selenium_test_cases.md`](../../project_documentation/selenium_evidence/selenium_test_cases.md)
- [`selenium_execution_report.md`](../../project_documentation/selenium_evidence/selenium_execution_report.md)
- [`selenium_test_results.csv`](../../project_documentation/selenium_evidence/selenium_test_results.csv)
- [`test screenshots`](../../project_documentation/selenium_evidence/)
- [`backend and regression report`](../../project_documentation/HELPNET_Testing_Report.docx)

The initial full run had four failures in fixtures that represented an NGO
with only a legacy approval flag. The fixtures were updated to create an
active, canonically approved NGO profile, and all four affected cases passed
on rerun. Two separate UI issues found during feature testing were also fixed
and retested: NGO file-validation feedback visibility and profile-page saving.

Production MySQL, deployment storage, SMTP delivery, performance, and
standalone JavaScript lint/build were not tested.

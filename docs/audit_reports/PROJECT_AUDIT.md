# HELPNET Project Audit

**Audit date:** 2026-11-03  
**Branch:** `samia`  
**Audited commit:** `e1523e3`  
**Source of truth:** Current Git checkout. No ZIP snapshot was used.  
**Validation update:** Selenium and backend tests were completed after the initial code-audit checklist below; the post-test results supersede its earlier "not run" notes.

## Scope and evidence

Inspected the Django apps, API routes, models, settings, templates, frontend
JavaScript, migrations, tests, current documentation, Git history, and tracked
file paths. The working tree was clean at the start of this audit. Findings
refer to code and records in this checkout unless explicitly called historical.

No SRS, SDS, teacher sample report, complete user-story register, approved
requirement-change log, stakeholder sign-off, full team contribution record,
budget record, or demonstration video was present. Requirements traceability
and submission details that depend on those artifacts are therefore incomplete.

## Status definitions

- **COMPLETE AND VERIFIED:** Full workflow has been tested through its intended
  user interface and backend.
- **IMPLEMENTED BUT NOT VERIFIED:** Implementation and automated backend tests
  exist, but the complete user-facing workflow was not verified here.
- **PARTIALLY IMPLEMENTED:** A known workflow, policy, or integration gap remains.
- **NOT IMPLEMENTED:** No implementation was found for the described capability.
- **BROKEN:** A confirmed defect prevents the described workflow.
- **BLOCKED:** Verification depends on unavailable infrastructure or evidence.
- **NOT APPLICABLE:** No matching feature is present or claimed.

The feature checklist records the initial audit assessment before the final
browser-test phase. Use the post-test validation update below and
`project_documentation/selenium_evidence/` for the latest execution evidence.

## Feature checklist

| Feature | Frontend | Backend/API and data | Validation and permissions | Tests/evidence | Status |
|---|---|---|---|---|---|
| Registration and login | Login, registration, password-reset pages and scripts exist. | Custom user model, JWT login/register/logout and reset APIs exist. | Serializer validation and privilege-assignment checks exist. | User permission/profile tests pass; no browser test executed. | IMPLEMENTED BUT NOT VERIFIED |
| Account management and user search | Profile, settings, search, profile switching, edit, deactivate, and reactivate controls exist. | User/profile APIs include owner-scoped lifecycle and supported role-detail editing. | Owner scoping and role checks are present. | Profile lifecycle/detail and permission tests pass; browser workflow not run. | IMPLEMENTED BUT NOT VERIFIED |
| Multiple role-specific profiles | Dashboard supports profile selection, editing, deactivation, and reactivation. | Profiles and active profile are modeled; legacy `User.role` remains in workflows. | Profile ownership and duplicate types are tested. | Profile lifecycle tests pass; role-dependent browser flow not run. | IMPLEMENTED BUT NOT VERIFIED |
| NGO registration and verification | Dashboard includes organization details, a required registration certificate, and optional supporting documents; admin review displays organization data and private document links. | Owner-scoped submission/status API, private document model/storage/download, legacy status data migration, and admin status/reason/timestamp actions exist. | File type/MIME/signature/size checks; owner/superuser document access; only an active approved NGO profile can coordinate; NGO status is separate from personal NID. | Backend tests cover submission, replacement, privacy, admin decisions, status gates, personal profiles, and switching. Integrated browser smoke exercised dashboard submission and admin additional-document review against mocked APIs; no live end-to-end run. | IMPLEMENTED BUT NOT VERIFIED |
| Identity/NID verification | Submission and admin pages/scripts exist; health review was wired to the admin page during this audit. | Private document upload/status/admin review APIs exist. | Admin-only review/download and owner submission controls exist. | Private verification download test and page wiring test pass. | IMPLEMENTED BUT NOT VERIFIED |
| Volunteer profiles and documents | Profile and certificate upload UI exist. | Volunteer profile and private document APIs/storage exist. | Role, owner, size, extension, and signature checks exist. | Volunteer API tests pass, including document workflow coverage. | IMPLEMENTED BUT NOT VERIFIED |
| Volunteer opportunities and signup | Browse, detail, signup, and coordinator pages/scripts exist. | Opportunity, signup, attendance, and message APIs/models exist. | NGO ownership, capacity, role, and duplicate checks exist. | Acceptance note and backend API tests pass; live browser flow not run. | IMPLEMENTED BUT NOT VERIFIED |
| Volunteer gatherings | Opportunities are implemented; no separate gathering model or requirement was found. | No independent gatherings API/model was identified. | Not established. | No distinct test/story evidence. | PARTIALLY IMPLEMENTED |
| Attendance and digital certificates | Coordinator attendance and certificate UI exist. | Attendance, certificate issuance, print view, and PDF API exist. | Coordinator, signup, completed-attendance, and download access checks exist. | Backend tests pass. Generic certificate POST now validates a body `event_id`. | IMPLEMENTED BUT NOT VERIFIED |
| Ratings and reviews | Rating and review UI exists in profiles and feature pages. | User and waste-collector ratings/APIs exist. | Score bounds, self-rating, and unique user-target rating are checked. | Rating tests pass; unrated averages are now represented as null. | PARTIALLY IMPLEMENTED |
| Blood donor search and profiles | Donor profile and search pages/scripts exist. | Donor profile/search APIs and availability model exist. | Search only returns available donors; donor updates are owner-scoped. | Blood tests pass. Legacy `available` query semantics are undefined and unused by the UI. | PARTIALLY IMPLEMENTED |
| Blood requests and donation history | Request creation/search pages exist. | Request, matching, completion, history, reports, and notifications are implemented. | Owner checks, upload validation, and history uniqueness exist. Documents are private and requester/superuser-only. | Blood API tests pass; migration test moves an existing sample document using temporary storage. | IMPLEMENTED BUT NOT VERIFIED |
| Notifications | Notification list/read UI exists. | Per-user list and read APIs exist. | Notifications are user-scoped. | Notification tests pass; end-to-end action links not browser-tested. | IMPLEMENTED BUT NOT VERIFIED |
| Goods exchange and messaging | Listing, details, interest, conversations, and chat pages/scripts exist. | Listings, interests, conversations, messages, and report APIs/models exist. | Listing owner and conversation participant permissions are present. | Goods tests pass; Selenium/browser workflow not run. | IMPLEMENTED BUT NOT VERIFIED |
| Goods-specific report model | No separate user-facing workflow is required to use this model. | `GoodsReport` exists, but the report endpoint writes generic `Report` records. | Generic moderation path exists. | Goods reporting tests cover the generic report path. | PARTIALLY IMPLEMENTED |
| Health questions and professionals | Question and professional pages/scripts exist; admin review script is included on the admin review page. | Question/reply, professional application, document, and review APIs exist. | Application authorization uses the legacy Citizen role. | Health API tests pass; role eligibility and full UI flow need confirmation. | PARTIALLY IMPLEMENTED |
| Farmer marketplace | Browse, create, details, and owner/admin edit UI exist. | Produce listing APIs/models support existing fields and availability updates. | Listing validations and owner/admin operations are covered. No image field exists. | Farmer update and availability-restoration tests pass; browser flow not run. | IMPLEMENTED BUT NOT VERIFIED |
| Waste pickup and collector reviews | Pickup, collector details, ratings, and review UI exists. | Pickup, collector, and rating APIs/models exist. | Owner-scoped operations and review access are tested. | Waste tests pass; Selenium/browser flow not run. | IMPLEMENTED BUT NOT VERIFIED |
| Reporting and moderation | Report submission and admin moderation UI exist. | Generic reports, content targets, moderation, and logs exist. | Superuser moderation controls are present. | Reports tests pass; the separate GoodsReport integration remains inconsistent. | PARTIALLY IMPLEMENTED |
| Admin dashboard and logs | Dashboard, verification, moderation, and log pages exist. | Admin endpoints and exports exist. | Admin/superuser checks exist in the backend. | Backend tests cover permissions; full dashboard interaction was not run. | IMPLEMENTED BUT NOT VERIFIED |
| Bangla/English localization | Shared localization support exists; dashboard roles/activities and selected NGO/farmer workflows have bilingual text. Coverage elsewhere varies. | Not applicable. | Not applicable. | Translation keys and NGO page toggle/script wiring inspected; no full browser language-switch acceptance run. | PARTIALLY IMPLEMENTED |
| MySQL production database | Database configuration exists. | MySQL backend is configured outside test runs. | Production configuration requires valid environment and database. | MySQL driver/server unavailable; tests use SQLite. | BLOCKED |
| Cloudinary storage | No active Cloudinary workflow was found. | Dependencies are declared but no configuration is active. | Not applicable. | No integration tests. | NOT IMPLEMENTED |
| Automated backup/restore | No application page. | Backup notes describe manual procedures; automation/drill not found. | Operational policy not verified. | No automated backup/restore test. | NOT IMPLEMENTED |
| Common app | No separate user-facing feature. | No model or route identified. | Not applicable. | One page-navigation test. | NOT APPLICABLE |

## Post-test validation update

- Backend: 128 tests passed.
- Selenium: 51 browser cases passed with 51 screenshots. The full directory run
  also included 47 HTTP-only rendered-page checks. Initial output was 94
  passed/4 fixture failures; all four affected cases passed after the fixture
  correction and targeted rerun. Final unique outcomes: 98 passed.
- Browser-tested workflows include profile creation/switch/edit/deactivate/
  reactivate; NGO submission, validation, owner/admin document access, and
  review decisions; bilingual profile content; authentication, blood,
  volunteer, goods, health, farmer, waste, ratings, notifications, and
  protected-page flows.
- These are local tests using Django `live_server`, SQLite, synthetic records,
  and test authentication setup. They do not establish production readiness.
- Production MySQL, deployed file storage, SMTP delivery, every admin
  verification/document-replacement journey, accessibility, performance, and
  standalone JavaScript lint/build remain untested.

## Database and migrations

Normal application configuration targets MySQL. Automated pytest execution
selects SQLite. Django system checks and migration-drift checks pass under the
test database. The MySQL driver is absent in this environment, so no live MySQL
connection, schema application, or data verification was performed.

The audit added migration `0004_private_blood_request_documents`, which moves
referenced existing blood-request documents from public media to private
storage, and `users.0007_userprofile_ngo_address_and_more`, which adds NGO
verification fields/documents and carries legacy approval statuses forward.
Migration behavior is covered by SQLite-based tests/checks but has not been
run against the project's live MySQL database.

## Repository evidence and limitations

- Current branch and commit: `samia`, `e1523e3`.
- Git history spans 2026-09-08 through 2026-11-02. It contains an explicit
  multi-profile implementation commit but does not document the original
  requirement, approval, or rationale for a role-based-to-account-based change.
- Nineteen private-upload files were tracked before this audit. They are now
  untracked from the current index, ignored, and retained locally. Earlier Git
  history is not rewritten.
- No `.env` file is tracked. The local environment file was not printed or
  copied into reports.
- The SQL backup contains no `INSERT INTO` statements; it appears schema-only
  from this limited check.
- A later Selenium run executed 51 browser cases and saved evidence; 47 other
  cases in the same suite are HTTP-only page-route checks. See the post-test
  update and generated execution report for final outcomes and limitations.

# HELPNET Code Change Log

This log records changes made during the 2026-11-03 audit. It is not a
requirement-change log. No commit or push was made.

| Change ID | Files/area | Change | Evidence |
|---|---|---|---|
| CC-01 | `.gitignore`, `backend/private_media/` | Ignore private uploads, profile pictures, and SQLite test database; remove 19 private-upload assets from the current Git index while preserving local copies. | Index count 0; working-copy count 19. |
| CC-02 | `backend/helpnet/settings.py`, `backend/.env.example` | Replace source-coded development key and unsafe defaults with environment configuration; require production secret/hosts; default production CORS closed and HTTPS redirects/cookies on; keep HSTS opt-in. Test runs use an isolated test-only key. | Django checks pass in test configuration; simulated production defaults are secure. |
| CC-03 | `frontend/js/admin-verification.js` | Render identity data and errors with safe DOM text; construct document links from an encoded request ID instead of interpolating server HTML. | Static inspection; full backend suite passes. |
| CC-04 | `frontend/pages/admin-verification.html`, `nid-verification.html`, `backend/apps/common/tests.py` | Load health-professional admin review script via Django static path on the correct page and remove the unrelated NID-page include. | Page rendering regression test passes. |
| CC-05 | `backend/apps/volunteer/views.py`, `tests.py` | Make collection certificate POST validate `event_id` from the body; return 400 when absent/invalid rather than raising a handler-argument error. | Volunteer regression tests pass. |
| CC-06 | `backend/apps/blood/models.py`, `views.py`, `urls.py`, new `storage.py`, migration `0004`, tests | Move blood request documents to private storage, add requester/superuser-only download route, restrict response links, validate file signature/type/extension/size, and migrate referenced old files. | Blood tests cover access, validation, and old-file move. |
| CC-07 | `backend/apps/ratings/views.py`, `tests.py`; `frontend/js/ratings.js`, `profile.js`, `blood.js` | Return null when no rating average exists and display an em dash rather than a fabricated rating. | Rating regression tests pass. |
| CC-08 | `README.md`, `PROJECT_SUMMARY.md` | Add accurate setup/testing guidance and update resolved issues, remaining gaps, security configuration, and test limitations. | Documentation reflects current checkout and audit results. |
| CC-09 | `backend/apps/users/`; `frontend/js/dashboard.js`; `frontend/pages/dashboard.html` | Add owner-scoped editing of supported volunteer/donor profile details, profile reactivation, NGO profile creation with pending status, selected-profile clearing on deactivation, and pending/rejected NGO status notices. Ensure profile cards still load after deactivating the selected profile leaves no legacy role. NGO coordinator actions require an active approved NGO profile. | Profile lifecycle, detail validation, approval/NID separation, and coordinator permission tests pass. |
| CC-10 | `backend/apps/farmer/views.py`, `backend/apps/farmer/tests.py`; `frontend/js/farmer.js`, `frontend/pages/produce-details.html` | Add owner/admin editing for existing product-listing fields and support toggling availability back on. The owner's marketplace list is not hidden by a stale cached role, and its Edit Product action opens the edit form directly. Product images remain unavailable because `ProduceListing` has no image field. | Farmer update and availability-restoration tests pass. |
| CC-11 | `frontend/js/i18n.js`, `dashboard.js`, `ngo-approval.js`, `ngo-approval.html`, `farmer.js`; `frontend/css/style.css`; `frontend/js/volunteer.js`; `backend/apps/common/tests.py` | Add Bangla/English coverage for dynamic dashboard role/activity text and the selected NGO/farmer workflows; add NGO-approval language toggle and translation test; restyle volunteer-opportunity navigation button. | Backend page-wiring test passes; browser-level visual and language-switch validation remains unavailable. |
| CC-12 | `backend/apps/users/{models.py,storage.py,serializers.py,views.py,urls.py,permissions.py}`, `migrations/0007_userprofile_ngo_address_and_more.py`; `backend/apps/volunteer/{views.py,tests.py}`; `backend/apps/users/tests/{test_ngo_verification.py,test_ngo_approval.py,test_profiles.py}`; `frontend/pages/{dashboard,ngo-approval}.html`; `frontend/js/{dashboard,ngo-approval,i18n}.js` | Add NGO organization/contact/representative fields and private registration/supporting-document records; validate PDF/JPG/PNG signatures, MIME and 10 MiB size; provide owner/superuser-only download, submitted/reviewed timestamps, statuses/reasons, resubmission/replacement, and admin review actions. Preserve legacy approvals with a data migration and make canonical verification status gate NGO coordinator features. Keep NGO and personal NID verification separate and allow the same account to switch among NGO and personal profiles. | `users.0007`; 128 backend tests pass, including file validation/access and profile-switching coverage; Django check and migration-drift check pass; mocked-API dashboard/admin browser smoke checks pass. No live MySQL migration or Selenium run. |

## Existing product/requirement decisions left open

- Availability-filter semantics for blood donor search.
- Whether ratings should be attached to a future transaction/interaction model.
- Whether GoodsReport should remain separate or all reports should use the generic
  moderation model.
- Health-professional application eligibility when accounts switch profiles.
- Broader Bangla/English coverage across legacy pages remains incomplete.
- NGO document access was smoke-tested with mocked APIs; live deployment
  storage/permissions and the MySQL migration remain unverified.
- Production HSTS, proxy/TLS, actual hostnames, CORS allow-list, and MySQL
  deployment settings.
- Whether prior Git history should be rewritten to purge previously tracked
  uploads and the old development key. No history rewrite was performed.

## Change-control statement

No historical requirement change was inferred from code changes in this audit.
The implementation commit adding multiple profiles is evidence of a feature
implementation, not proof of an approved requirement transition.

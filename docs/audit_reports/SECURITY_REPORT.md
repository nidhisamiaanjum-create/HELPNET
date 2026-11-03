# HELPNET Security Report

**Scope:** Current Git checkout and local configuration shape. No secret values,
passwords, or document contents are included in this report.

## Findings and remediation

| ID | Severity | Finding | Current status |
|---|---|---|---|
| SEC-01 | High | Nineteen private user uploads were tracked in Git. | Removed from current index; local copies preserved and upload directory ignored. Earlier Git history still contains prior objects. |
| SEC-02 | High | A development secret was hardcoded in settings; DEBUG, host, and CORS defaults were unsuitable for production. | Current settings are environment-backed; DEBUG defaults off; production secret length/hosts are required; wildcard CORS is off by default. Rotate any key that may have been used in a deployed environment. |
| SEC-03 | High | Verification admin page inserted user-controlled identity fields and error messages as HTML. | Replaced with safe DOM text nodes. No dynamic `innerHTML` remains in that script. Browser-level regression test was unavailable. |
| SEC-04 | High | Blood-request documents were stored under public media and API responses exposed their public URL. MIME type was trusted without matching file bytes. | New uploads use private storage and signature checks; document endpoint requires owner or superuser; legacy referenced files are moved by migration. |
| SEC-05 | Medium | Health-professional review script was not loaded from the admin review page and was incorrectly referenced by the NID page. | Corrected static include and added page test. |
| SEC-06 | Medium | Production-mode Django deployment check reports no HSTS policy. | Intentionally left opt-in until the public domain, HTTPS termination, and subdomain policy are confirmed. |
| SEC-07 | Medium | Production MySQL configuration and private-file migration were not tested against a live database/storage deployment. | Blocked by missing local MySQL driver and deployment access. |
| SEC-08 | High | NGO verification documents required private storage and explicit access control. | Added private storage with no public URL, authenticated owner/superuser download endpoint, file signature/MIME/size checks, and admin review URLs. Backend tests verify owner/admin access and refusal for another user; live deployment storage remains unverified. |

## Checks performed

- `.env`/private-upload tracking: `.env` is ignored and not tracked; private
  uploads were tracked before this audit and are now absent from the current
  index.
- SQL: no raw SQL execution, `.raw()`, or `RawSQL()` use was found under
  `backend/apps/`.
- File uploads: blood, volunteer, and NGO uploads enforce size/type/signature
  rules; identity, health credentials, and NGO verification documents use
  private storage handlers.
- Authorization: backend tests cover user/profile ownership, admin actions,
  volunteer event membership, and document-download permissions.
- CORS and host settings: environment-based, production wildcard CORS disabled,
  explicit hosts required when DEBUG is off.
- SQL injection: ORM-based query construction was observed; no raw SQL use found
  in the application apps.
- Frontend injection: the verification admin sink was removed. Other reviewed
  dynamic cards use `textContent` or escaped content; no broad browser security
  scan was available.

## Required operator actions

1. Generate a fresh random Django `SECRET_KEY` of at least 50 characters in each
   deployed environment. Do not paste it into source, issue reports, or chat.
2. Set `DEBUG=False`, exact production `ALLOWED_HOSTS`, and the smallest needed
   `CORS_ALLOWED_ORIGINS` list.
3. Configure HTTPS redirects/cookies for the actual proxy/TLS topology.
4. Enable HSTS only after verifying HTTPS for the entire domain and deciding
   whether subdomains are in scope.
5. Apply migration `blood.0004` with access to the existing public media files;
   verify counts and access before deleting any backups.
6. Apply migration `users.0007` and configure `PRIVATE_MEDIA_ROOT` with
   restricted filesystem permissions before enabling NGO document uploads.
7. Coordinate a Git-history purge for the historical uploads/development key
   with all repository users. This changes shared history and would require an
   approved force-push; it was not performed.
8. Rotate any credentials/secrets that may have been valid or used in the past.

## Residual risk

Untracking files does not erase prior Git commits, clones, caches, or remote
objects. No commit or push was made, and no secret or upload was sent to an
external system during this audit.

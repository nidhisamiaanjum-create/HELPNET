# HELPNET Requirement Change Log

**Document status:** Draft; requires project-team and stakeholder confirmation  
**Prepared:** 2026-11-03

## Purpose and evidence limits

This log separates formally evidenced requirement changes from implementation
observations and audit fixes. No SRS, approved change request, full user-story
register, meeting minutes, or stakeholder sign-off was found in the repository.
Therefore, no unverified change is represented as approved.

## Candidate requirement changes

### RCL-01: Multiple profiles and active-profile switching

- **Area:** User accounts and profiles
- **Observed implementation:** A user can hold multiple profiles and select an
  active profile. Git history contains a multi-profile implementation commit
  dated 2026-10-25 and a profile-switching fix dated 2026-10-28.
- **Prior requirement/baseline:** Not present in the repository.
- **Reason for change:** Not documented.
- **Requester and approval:** Not documented.
- **Affected users/modules:** Users, role-sensitive APIs, profile UI, and
  potentially authorization rules.
- **Implementation state:** Implemented in code; backend tests cover profile
  creation, ownership, and switching.
- **Status:** **Candidate change only - approval and original baseline require
  team confirmation.**
- **Acceptance evidence:** No stakeholder acceptance record found.

### RCL-02: Blood-request document access policy

- **Area:** Blood request supporting documents
- **Confirmed rule during audit:** Access is limited to the request owner
  (requester) and administrators.
- **Approval evidence:** The user explicitly selected this access policy during
  the audit. The user's authority to approve product requirements was not
  established by repository evidence.
- **Affected users/modules:** Blood request creation, document storage,
  download API, and migration of referenced legacy documents.
- **Implementation state:** Implemented with private storage and requester /
  superuser checks; regression tests pass.
- **Status:** **User-confirmed for this audit; formal stakeholder acceptance
  should still be recorded by the project team.**

## Audit changes that are not recorded as requirement changes

The following changes correct implementation defects or security behavior.
They do not establish a new user requirement:

- Environment-backed production settings and safer defaults.
- Safe DOM rendering on the verification admin page.
- Correct static-script inclusion for health-professional review.
- Accepting and validating `event_id` on the volunteer certificate collection
  endpoint.
- Consistent null averages for users without ratings.
- Removing private uploads from the current Git index.
- Updating setup, audit, and testing documentation.

The follow-up implementation request also resulted in profile editing and
reactivation, pending/rejected NGO dashboard messaging, editing supported
farmer listing fields, selected Bangla/English translations, and volunteer
opportunity button styling. These are documented as current implementation
work in the [Code Change Log](../audit_reports/CODE_CHANGE_LOG.md), not as
formally approved requirement changes; no approved baseline or acceptance
record was supplied. NGO uploads were explicitly excluded from the requested
scope, and produce image edits are unavailable because the current model has
no image field.

See [Code Change Log](../audit_reports/CODE_CHANGE_LOG.md) and
[Bug Tracker](../audit_reports/BUG_TRACKER.md) for affected files and tests.

## Proposed change-request template

Complete this record for every change that the project team confirms as an
approved requirement change:

- **Change ID:**
- **Request date:**
- **Requester:**
- **Requirement / story ID:**
- **Original approved requirement:**
- **Requested requirement:**
- **Business reason:**
- **Affected users and workflows:**
- **Security/privacy impact:**
- **Database/API/UI impact:**
- **Effort and schedule impact:**
- **Alternatives considered:**
- **Decision and approver:**
- **Acceptance criteria:**
- **Implementation reference / commit:**
- **Tests and results:**
- **Acceptance evidence and date:**

## Outstanding confirmation

The project team should locate the approved requirements baseline and confirm
whether RCL-01 represents a real requirement change. If no approved record can
be found, retain it as an implementation-history note rather than asserting a
change from role-based to multi-profile registration. The team should also
record formal acceptance for RCL-02 if the audit user's decision is not itself
the authorized stakeholder approval.

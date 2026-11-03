# HELPNET Video Demonstration Script

**Status:** Recording script only - no video has been recorded.  
**Target length:** 7-9 minutes  
**Audience:** Project supervisor, assessors, and stakeholders

## Before recording

- Start the application using a prepared test environment and test accounts.
- Use synthetic data only. Do not show real identity documents, email addresses,
  phone numbers, passwords, API tokens, secret settings, or private uploads.
- Prepare accounts for a regular user, approved NGO coordinator, volunteer,
  and administrator if these flows are to be shown.
- Confirm each account is authorized for the exact workflow demonstrated.
- Use a staging/local environment with no production data.
- If an account or page is unavailable, state that it was not demonstrated;
  do not simulate success with a fabricated screen.
- Hide browser developer tools and environment files unless intentionally
  explaining a non-sensitive configuration setting.

## Script

### 0:00-0:35 - Opening and scope

**On screen:** HELPNET landing page.

**Narration:**  
"This is HELPNET, a Django-based community services platform. It brings
together volunteering, blood donation, goods exchange, health questions,
farmer listings, and waste pickup. This demonstration uses a test environment
and synthetic data. It focuses on workflows that are available in the current
build; it is not a claim that every feature has been accepted or deployed to
production."

### 0:35-1:20 - Sign in and profile overview

**On screen:** Sign in with a prepared test user; show the profile or dashboard.

**Narration:**  
"I am signing in with a prepared test account. The application uses
authenticated API requests for protected actions. This dashboard provides
entry points to the community-service areas available to this account. The
profile screen shows the account information and profile controls."

**Action:** If test data is available, show profile selection without exposing
private account information.

**Narration:**  
"The project supports multiple profiles and an active-profile selection. Access
to protected operations is also checked by the backend, not only hidden in the
interface."

### 1:20-2:20 - Volunteer opportunity and signup

**On screen:** Sign in as an approved NGO coordinator; show an existing
synthetic opportunity. Then use a volunteer test account to open its details.

**Narration:**  
"An approved NGO coordinator can publish and manage opportunities. A volunteer
can browse open opportunities and request a place while the event has capacity.
The backend rejects duplicate signups, closed events, and signups after the
capacity is reached."

**Action:** Demonstrate signup only if a seeded test event is available. If
not, show the page and describe the tested rules without claiming a live
signup.

### 2:20-3:05 - Volunteer attendance and certificate

**On screen:** Coordinator attendance view and a test certificate, if available.

**Narration:**  
"Coordinators can record attendance for signed-up volunteers. Certificate
issuance is tied to the event workflow. The collection endpoint now validates
the event identifier supplied in the request, and the backend test suite
covers this input."

**Action:** Do not issue or alter a real certificate during the recording.

### 3:05-4:00 - Blood donation and privacy

**On screen:** Blood donor/request interface using synthetic entries. Do not
open or display a real uploaded document.

**Narration:**  
"The blood-donation area supports donor profiles and blood requests. Supporting
documents are stored privately. In this build, the requester and administrators
are the only users authorized to retrieve the request document. The access
rule and file-validation behavior are covered by backend regression tests."

**Action:** If showing a download, use a harmless synthetic sample on a local
test environment and verify the account is authorized. Otherwise, describe the
policy without opening a file.

### 4:00-4:50 - Goods and communication

**On screen:** Goods listing and conversation page populated with synthetic data.

**Narration:**  
"The goods area supports listings, interest, and conversations between the
listing owner and an interested user. Message access is limited to participants.
The project also provides reporting and moderation workflows."

### 4:50-5:35 - Health, farmer, and waste areas

**On screen:** Briefly show the relevant navigation pages or safe test entries.

**Narration:**  
"Other implemented areas include health questions and professional
applications, produce listings for the farmer marketplace, and waste pickup
requests with collector information. Each area has backend APIs and database
models. The full browser workflows still need end-to-end verification in a
supported browser environment."

### 5:35-6:20 - Administration and verification

**On screen:** Administrator review queue with synthetic identities only.

**Narration:**  
"Administrative pages support identity review, NGO approval, and content
moderation. User-provided identity text is rendered as text rather than
executable HTML. Sensitive document access is protected by backend
authorization. This screen uses synthetic review data."

### 6:20-7:15 - Testing and limitations

**On screen:** A prepared slide or report excerpt showing the current test
summary; avoid terminals containing environment variables.

**Narration:**  
"The latest backend test run passed 115 tests. Django system and migration
checks also passed using the SQLite test configuration. Ninety-one Selenium
tests were collected but not run in this environment because a browser and
WebDriver were unavailable. MySQL-backed production checks were also blocked
by the missing local MySQL driver. These limitations are documented in the
audit report."

### 7:15-7:50 - Close

**On screen:** HELPNET landing page or project title slide.

**Narration:**  
"This concludes the HELPNET demonstration. The codebase contains a broad set
of community-service workflows and automated backend coverage. Before a final
production or academic acceptance claim, the team should complete browser
testing, validate the MySQL deployment and private-file migration, confirm
the requirements and contribution records, and record stakeholder sign-off."

## Recording checklist

- [ ] Demonstration is made with synthetic data only.
- [ ] No credential, token, personal document, or private upload is visible.
- [ ] Any unavailable flow is explicitly labeled not demonstrated.
- [ ] Test results are quoted accurately: 115 backend tests passed; 91 Selenium
  tests collected but not run.
- [ ] No production-readiness or stakeholder-acceptance claim is made without
  evidence.
- [ ] Obtain required team/stakeholder permission before publishing the video.

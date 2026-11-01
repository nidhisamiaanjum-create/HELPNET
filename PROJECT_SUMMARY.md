# HELPNET Project Summary

## Overview

HELPNET is a Bangladesh-focused community services platform that connects people with local support for blood donation, volunteering, health, goods exchange, farming, and waste pickup. It provides authenticated APIs and a Django-template frontend, with separate moderation and verification workflows.

**Stack:** Python; Django `>=5.2,<5.3`; Django REST Framework `>=3.16,<3.17`; SimpleJWT `>=5.5,<6`; MySQL for normal runs and SQLite for tests; server-rendered Django templates with vanilla JavaScript, HTML, and CSS. Dependency versions are ranges, not exact pins; no Python version or frontend package manager is specified.

## Folder structure

```text
backend/
  helpnet/                 Django settings, root URL routing, ASGI/WSGI
  apps/                    Django apps for users, blood, goods, health,
                           farmer, waste, volunteer, ratings, reports,
                           notifications, verification, and common
  media/, private_media/   Local public and restricted uploads
frontend/
  pages/                   Django HTML templates for the app and admin pages
  js/                      Shared and feature-specific browser scripts
  css/                     Shared and certificate-print styles
tests/selenium/             Browser-level tests
docs/                       Setup-adjacent, testing, acceptance, and triage docs
```

## Features

| Area | User-facing and backend behavior | Main implementation |
|---|---|---|
| Accounts and profiles | Register/login by email or phone; password reset; JWT sessions; user profiles, profile switching, privacy settings, user search, and NGO profile approval | `backend/apps/users/`; `frontend/pages/{login,register,forgot-password,reset-password,profile,settings,user-search,ngo-approval}.html`; `frontend/js/{auth,api,profile,user-search,ngo-approval}.js` |
| Identity verification | Submit NID/passport/birth-certificate documents, check status, and allow admins to review documents, approve/reject, and inspect action logs | `backend/apps/verification/`; `frontend/pages/{nid-verification,admin-verification,admin-logs}.html`; `frontend/js/{nid-verification,admin-verification,admin-logs}.js` |
| Blood donation | Maintain donor profiles, search donors, post requests, match donors, notify matches, complete/close requests, and view donation history | `backend/apps/blood/`; `frontend/pages/blood.html`; `frontend/js/blood.js` |
| Goods exchange | Browse and post listings, express interest, manage listing status, create participant conversations/messages, and report listings | `backend/apps/goods/`; `frontend/pages/{goods-list,create-goods,goods-details,goods-conversations,goods-chat}.html`; `frontend/js/{goods,goods-chat}.js` |
| Health | Post health questions and replies; browse verified professionals; submit professional credentials for admin review | `backend/apps/health/`; `frontend/pages/{health-questions,create-health-question,health-question-details,health-professionals}.html`; `frontend/js/health.js` |
| Farmer market | Browse, create, update and report produce listings; view local price ranges | `backend/apps/farmer/`; `frontend/pages/{farmer-market,create-produce,produce-details}.html`; `frontend/js/farmer.js` |
| Waste pickup | Create/manage pickup requests; find collectors; view collector details and submit collector ratings/reviews | `backend/apps/waste/`; `frontend/pages/{waste-pickup,collector-details}.html`; `frontend/js/waste.js` |
| Volunteering | NGO coordinators publish opportunities; volunteers sign up; coordinators manage attendance, messages and certificates; search volunteer profiles and export admin data | `backend/apps/volunteer/`; `frontend/pages/{volunteer-opportunities,volunteer-opportunity-details,create-opportunity,volunteer-search,volunteer-profile,volunteer-message,volunteer-attendance,volunteer-certificate,volunteer-certificate-print,admin-volunteers}.html`; `frontend/js/{volunteer,volunteer-admin,volunteer-profile,volunteer-certificate-print}.js` |
| Ratings, notifications, and moderation | Rate users, view rating summaries, receive/read notifications, submit content reports, and let superusers review/edit/remove reported content | `backend/apps/{ratings,notifications,reports}/`; `frontend/pages/{ratings,notifications,admin-moderation}.html`; `frontend/js/{ratings,notifications,admin-moderation,trust-component}.js` |
| Shared UI and administration | Landing page, dashboard, navigation, district selection, Bangla/English localization, admin dashboard and logs | `frontend/pages/{home,dashboard,admin-dashboard,admin-logs}.html`; `frontend/js/{api,app,dashboard,navigation,districts,i18n,admin-dashboard,admin-logs}.js`; `frontend/css/style.css` |

`frontend/js/api.js` provides shared bearer-token requests, but some pages use direct `fetch`. `frontend/js/i18n.js` supports Bangla and English. `frontend/pages/settings.html` and some admin pages include inline scripts.

## API endpoints

All paths below are mounted below `/api/` unless the full path is shown. JWT authentication and `IsAuthenticated` are the DRF defaults; public and role/owner-limited exceptions are noted. Successful custom endpoints usually return `{success, data, message}`; generic DRF views return serializer JSON directly. Error responses include framework validation/authentication errors. Route line references point to app URL configurations; app prefixes are composed in `backend/helpnet/urls.py:26-50`.

| Method | Path | Description | Auth required | Request params/body | Response | File:line |
|---|---|---|---|---|---|---|
| GET | `/api/` | API status/welcome and endpoint listing | No | None | JSON status object | `backend/helpnet/urls.py:13-21` |
| POST | `/api/auth/register/` | Register citizen or NGO | No | `full_name,email,phone_number,password,location,account_type` | 201; user and profiles; NGO approval pending message | `backend/apps/users/urls.py:16-43`; `views.py:32-76` |
| POST | `/api/auth/login/` | Login with email or phone | No | `identifier,password` | User data and access/refresh JWTs | `backend/apps/users/urls.py:16-43`; `views.py:86-199` |
| POST | `/api/auth/logout/` | Blacklist refresh token | Yes | `refresh` | Success with null data | `backend/apps/users/urls.py:16-43`; `views.py:202-381` |
| POST | `/api/auth/password-reset/` | Request password reset email | No | `email` | Generic success, including unknown email | `backend/apps/users/urls.py:16-43`; `views.py:202-381` |
| POST | `/api/auth/password-reset-confirm/` | Set new password from reset token | No | `uid,token,new_password` | Success with null data | `backend/apps/users/urls.py:16-43`; `views.py:202-381` |
| GET, PATCH | `/api/auth/me/` | Read/update current user profile | Yes | PATCH writable profile fields | Wrapped profile object | `backend/apps/users/urls.py:16-43`; `views.py:383-437` |
| GET, POST | `/api/auth/profiles/` | List/create profiles (NGO profile creation is disallowed here) | Yes | POST `profile_type`, optional `display_name,details` | Wrapped profile list/object | `backend/apps/users/urls.py:16-43`; `views.py:438-538` |
| GET, PUT, PATCH, DELETE | `/api/auth/profiles/<int:id>/` | Read/update/deactivate own profile | Yes; owner-scoped | Profile serializer fields; DELETE has no body | Serializer object; DELETE 204 | `backend/apps/users/urls.py:16-43`; `views.py:438-538` |
| GET, PUT | `/api/auth/active-profile/` | Read/select active profile | Yes | PUT `profile_id` | Wrapped profile or null | `backend/apps/users/urls.py:16-43`; `views.py:438-538` |
| GET | `/api/auth/ngo-profiles/pending/` | List pending NGO profiles | Superuser | None | Pending profiles and count | `backend/apps/users/urls.py:16-43`; `views.py:539-619` |
| PATCH | `/api/auth/ngo-profiles/<int:profile_id>/approval/` | Approve/reject NGO profile | Superuser | `approval_status=approved|rejected` | Profile/status result | `backend/apps/users/urls.py:16-43`; `views.py:539-619` |
| GET | `/api/users/search/` | Search other users | Yes | Query `q` | Up to 20 matching user summaries | `backend/apps/users/urls.py:16-43`; `views.py:620-675` |
| GET | `/api/users/<uuid:user_id>/` | Read public user profile | Yes | UUID path parameter | Wrapped profile and rating metrics | `backend/apps/users/urls.py:16-43`; `views.py:620-675` |
| GET | `/api/waste/collectors/available/` | Find volunteer collectors | Yes | Query `area` | Wrapped collector summaries | `backend/apps/waste/urls.py:14-49`; `views.py:21-270` |
| GET, POST | `/api/waste/requests/` | List/create pickup requests | Yes | GET `area,status`; POST request fields for waste, location, pickup, status/notes, optional collector | Generic serialized list/object | `backend/apps/waste/urls.py:14-49`; `views.py:21-270` |
| GET, PUT, PATCH, DELETE | `/api/waste/requests/<uuid:id>/` | Read/update/delete pickup request | Yes; owner/role rules | Update request fields | Serialized request | `backend/apps/waste/urls.py:14-49`; `views.py:21-270` |
| GET, POST | `/api/waste/collectors/` | List/share a collector | Yes | GET `area`; POST `name,phone,area,waste_types,notes` | Generic serialized list/object | `backend/apps/waste/urls.py:14-49`; `views.py:21-270` |
| GET | `/api/waste/collectors/<uuid:collector_id>/` | Read collector/volunteer details | Yes | Collector UUID | Wrapped details; volunteer contact is visibility-gated | `backend/apps/waste/urls.py:14-49`; `views.py:21-270` |
| GET, POST | `/api/waste/collectors/<uuid:collector_id>/ratings/` | List/create collector rating | Yes | POST `rating,review` | Rating array or created rating | `backend/apps/waste/urls.py:14-49`; `views.py:21-270` |
| GET, POST | `/api/farmer/produce/` | Browse/create produce listing | Yes; Farmer role to create | GET `search,location,category,availability`; POST `produce_name,category,price,unit,quantity,availability,location,description` | Generic serialized list/object | `backend/apps/farmer/urls.py:11-15`; `views.py:18-130` |
| GET, PUT, PATCH, DELETE | `/api/farmer/produce/<uuid:id>/` | Read/update/delete produce listing | Yes; owner or superuser for writes | Listing fields for updates | Serialized listing | `backend/apps/farmer/urls.py:11-15`; `views.py:18-130` |
| GET | `/api/farmer/produce/<uuid:id>/price-range/` | Compare local/category prices | Yes | Listing UUID | Wrapped min/max/average/count | `backend/apps/farmer/urls.py:11-15`; `views.py:18-130` |
| POST | `/api/farmer/produce/<uuid:id>/reports/` | Report a produce listing | Yes | `description` | Wrapped report ID | `backend/apps/farmer/urls.py:11-15`; `views.py:18-130` |
| GET | `/api/farmer/my-produce/` | List current user's produce | Yes | None | Wrapped list and count | `backend/apps/farmer/urls.py:11-15`; `views.py:18-130` |
| GET, POST | `/api/ratings/`, `/api/ratings/create/` | List/create user ratings | Yes | GET `user_id` or `rated_user`; POST `rated_user,rating` or `score`, optional `comment` | Wrapped rating data | `backend/apps/ratings/urls.py:5-12`; `views.py:15-166` |
| GET | `/api/ratings/users/<uuid:user_id>/`, `/api/ratings/<uuid:user_id>/` | List ratings for user (long and short aliases) | Yes | User UUID | Wrapped rating array | `backend/apps/ratings/urls.py:5-12`; `views.py:15-166` |
| GET | `/api/ratings/users/<uuid:user_id>/average/`, `/api/ratings/<uuid:user_id>/average/` | Get average rating (long and short aliases) | Yes | User UUID | Wrapped average and count | `backend/apps/ratings/urls.py:5-12`; `views.py:15-166` |
| GET | `/api/ratings/summary/<uuid:user_id>/` | Get rating summary and recent reviews | Yes | User UUID | Wrapped summary and up to 10 reviews | `backend/apps/ratings/urls.py:5-12`; `views.py:125-166` |
| GET, POST | `/api/reports/` | List/create reports | Yes | Create serializer-writable report fields; reporter assigned server-side | Generic serialized reports | `backend/apps/reports/urls.py:5-6`; `views.py:14-420` |
| GET, POST | `/api/reports/moderation/` | Review/edit/remove reported content | Superuser | GET `content_type`; POST `report_id,action`, optional `changes`; direct moderation uses `content_type,object_id,reason` | Wrapped moderation summaries/result; actions audit-logged | `backend/apps/reports/urls.py:5-6`; `views.py:14-420` |
| GET, PUT | `/api/blood/donor-profile/` | Read/update own donor profile | Yes | PUT `blood_group,area,availability` or legacy `is_available` | Wrapped donor | `backend/apps/blood/urls.py:7-14`; `views.py:19-400` |
| GET | `/api/blood/donors/` | Search donors | Yes | Query `blood_group,area,search` (also accepts `available`, currently ineffective) | Wrapped donor list | `backend/apps/blood/urls.py:7-14`; `views.py:19-400` |
| GET, POST | `/api/blood/requests/` | List open requests/create a request | Yes | POST `blood_group,area,hospital`, optional `details,supporting_document` (multipart) | Wrapped request; creates notifications for matching donors | `backend/apps/blood/urls.py:7-14`; `views.py:19-400` |
| GET | `/api/blood/requests/<uuid:request_id>/matches/` | Match donors to request | Yes; requester only | Request UUID | Wrapped donor list | `backend/apps/blood/urls.py:7-14`; `views.py:19-400` |
| POST | `/api/blood/requests/<uuid:request_id>/complete/` | Record completed donation | Yes; requester only | `donor_id` | Wrapped completed request | `backend/apps/blood/urls.py:7-14`; `views.py:19-400` |
| POST | `/api/blood/requests/<uuid:request_id>/close/` | Close blood request | Yes; requester only | Request UUID | Wrapped closed request | `backend/apps/blood/urls.py:7-14`; `views.py:19-400` |
| POST | `/api/blood/requests/<uuid:request_id>/reports/` | Report blood request | Yes | `description` | Wrapped report ID | `backend/apps/blood/urls.py:7-14`; `views.py:19-400` |
| GET | `/api/blood/donations/` | List current user's donation history | Yes | None | Wrapped donation array | `backend/apps/blood/urls.py:7-14`; `views.py:19-400` |
| GET | `/api/notifications/` | List current user's notifications | Yes | None | Wrapped notification list | `backend/apps/notifications/urls.py:7-8`; `views.py:10-60` |
| POST, PATCH | `/api/notifications/<uuid:notification_id>/read/` | Mark own notification read | Yes; owner-scoped | Notification UUID; no body | Wrapped notification | `backend/apps/notifications/urls.py:7-8`; `views.py:10-60` |
| GET, POST | `/api/goods/listings/` | Browse/create goods listings | Yes | POST listing fields and optional image | Wrapped listing/list | `backend/apps/goods/urls.py:5-12`; `views.py:24-196` |
| GET | `/api/goods/listings/<int:listing_id>/` | Read listing | Yes | Listing ID | Wrapped listing | `backend/apps/goods/urls.py:5-12`; `views.py:24-196` |
| PATCH | `/api/goods/listings/<int:listing_id>/status/` | Change own listing status | Yes; owner-only | `status` | Wrapped result | `backend/apps/goods/urls.py:5-12`; `views.py:24-196` |
| POST | `/api/goods/listings/<int:listing_id>/interest/` | Express interest/start or reuse conversation | Yes | Listing ID; no required body | Interest and conversation details | `backend/apps/goods/urls.py:5-12`; `views.py:24-196` |
| GET | `/api/goods/listings/<int:listing_id>/interested-users/` | List interested users | Yes; listing owner | Listing ID | Wrapped user/conversation list | `backend/apps/goods/urls.py:5-12`; `views.py:24-196` |
| GET | `/api/goods/conversations/` | List current user's conversations | Yes | None | Wrapped conversations with latest message | `backend/apps/goods/urls.py:5-12`; `views.py:24-196` |
| GET, POST | `/api/goods/conversations/<int:conversation_id>/` | Read conversation/send message | Yes; participant | POST `message` (1–2000 characters) | Wrapped conversation or created message | `backend/apps/goods/urls.py:5-12`; `views.py:24-196` |
| POST | `/api/goods/listings/<int:listing_id>/reports/` | Report goods listing | Yes | `reason`, optional `description` | Serialized generic report | `backend/apps/goods/urls.py:5-12`; `views.py:24-196` |
| GET, POST | `/api/health/questions/` | List/create health questions | Yes | POST `title,description,category` | Wrapped question list/object | `backend/apps/health/urls.py:6-13`; `views.py:27-278` |
| GET | `/api/health/questions/<int:question_id>/` | Read question detail | Yes | Question ID | Wrapped question | `backend/apps/health/urls.py:6-13`; `views.py:27-278` |
| GET, POST | `/api/health/questions/<int:question_id>/replies/` | List/create question replies | Yes | POST `reply` | Wrapped replies | `backend/apps/health/urls.py:6-13`; `views.py:27-278` |
| GET | `/api/health/professionals/` | List verified health professionals | Yes | None | Wrapped professional list | `backend/apps/health/urls.py:6-13`; `views.py:27-278` |
| GET, POST | `/api/health/professionals/application/` | Read/submit professional application | Citizen role | POST multipart credential and contact fields | Application status/result | `backend/apps/health/urls.py:6-13`; `views.py:27-278` |
| GET | `/api/health/professionals/admin/pending/` | List pending professional applications | Superuser | None | Wrapped pending list | `backend/apps/health/urls.py:6-13`; `views.py:27-278` |
| GET | `/api/health/professionals/admin/<int:professional_id>/document/` | Download credential document | Superuser | Professional ID | Attachment stream | `backend/apps/health/urls.py:6-13`; `views.py:27-278` |
| PATCH | `/api/health/professionals/<int:professional_id>/verification/` | Approve/reject professional application | Superuser | `action` or `verification_status`; rejection `reason` | Wrapped result | `backend/apps/health/urls.py:6-13`; `views.py:27-278` |
| GET, POST | `/api/volunteer/opportunities/` | Browse/create volunteer opportunities | Yes; create requires approved active NGO coordinator or superuser | GET `all=true`; POST event fields | Wrapped opportunity list/object | `backend/apps/volunteer/urls.py:5-19`; `views.py:20-359` |
| GET | `/api/volunteer/my-events/` | List joined/coordinated events | Yes | `coordinated=true` for coordinator list | Wrapped event list | `backend/apps/volunteer/urls.py:5-19`; `views.py:20-359` |
| GET, PATCH | `/api/volunteer/opportunities/<int:event_id>/` | Read event/update its status | Yes; coordinator for update | PATCH `status` | Wrapped event | `backend/apps/volunteer/urls.py:5-19`; `views.py:20-359` |
| GET, POST | `/api/volunteer/opportunities/<int:event_id>/signup/` | List signups or sign up | Yes; coordinator to list, Volunteer role to sign up | POST no required body | Wrapped signup data | `backend/apps/volunteer/urls.py:5-19`; `views.py:20-359` |
| GET, POST | `/api/volunteer/opportunities/<int:event_id>/attendance/` | View/manage attendance | Yes; coordinator-only | POST `volunteer_id,action=check_in|check_out` | Wrapped attendance | `backend/apps/volunteer/urls.py:5-19`; `views.py:20-359` |
| GET, POST | `/api/volunteer/opportunities/<int:event_id>/messages/` | List/send event messages | Yes; event participants | POST `message` | Wrapped messages | `backend/apps/volunteer/urls.py:5-19`; `views.py:20-359` |
| GET, POST | `/api/volunteer/opportunities/<int:event_id>/certificates/` | List/issue event certificates | Yes; coordinator-only | POST `volunteer_id`; completed attendance required | Wrapped certificates | `backend/apps/volunteer/urls.py:5-19`; `views.py:20-359` |
| GET, POST | `/api/volunteer/certificates/` | List current/coordinated certificates | Yes | POST handler expects `event_id`, but this route does not provide it | Wrapped certificate list; POST route mismatch | `backend/apps/volunteer/urls.py:5-19`; `views.py:20-359` |
| GET | `/api/volunteer/certificates/<int:certificate_id>/pdf/` | Download certificate PDF | Yes; volunteer, coordinator or staff | Certificate ID | PDF attachment | `backend/apps/volunteer/urls.py:5-19`; `views.py:20-359` |
| GET, PUT | `/api/volunteer/profile/` | Read/update volunteer profile | Yes; Volunteer role for update | PUT skills, availability, location, blood group, certificate text | Wrapped profile | `backend/apps/volunteer/urls.py:5-19`; `views.py:20-359` |
| GET, POST | `/api/volunteer/profile/documents/` | List/upload private profile documents | Yes; Volunteer role | POST multipart `file` | Wrapped document list/object | `backend/apps/volunteer/urls.py:5-19`; `views.py:20-359` |
| GET | `/api/volunteer/profile/documents/<int:document_id>/download/` | Download own private document | Yes; owner Volunteer | Document ID | Attachment stream | `backend/apps/volunteer/urls.py:5-19`; `views.py:20-359` |
| GET | `/api/volunteer/search/` | Search volunteer profiles | Yes; approved NGO coordinator or superuser | `skills,availability,location,participation_history,event_id` | Wrapped profile list | `backend/apps/volunteer/urls.py:5-19`; `views.py:20-359` |
| GET | `/api/volunteer/admin/` | Admin volunteer listing | Superuser | Implemented filters | Profile data | `backend/apps/volunteer/urls.py:5-19`; `views.py:20-359` |
| GET | `/api/volunteer/admin/export/`, `/api/admin/volunteers/export/` | Export volunteer data as CSV | Superuser | Implemented filters | CSV download | `backend/apps/volunteer/urls.py:5-19`; `backend/helpnet/urls.py:36-37` |
| GET | `/api/admin/volunteers/` | Admin volunteer listing alias | Superuser | Implemented filters | Profile data | `backend/helpnet/urls.py:36-37` |
| GET | `/api/verification/` | Render verification page | No explicit API auth | None | HTML page | `backend/apps/verification/urls.py:7-42`; `views.py:17-342` |
| POST | `/api/verification/submit/` | Submit identity document | Yes | Multipart `document_type,document` | Wrapped verification request summary | `backend/apps/verification/urls.py:7-42`; `views.py:17-342` |
| GET | `/api/verification/status/` | Read latest verification status | Yes | None | Wrapped status; defaults to unverified | `backend/apps/verification/urls.py:7-42`; `views.py:17-342` |
| GET | `/api/verification/admin/` | List verification requests | Superuser | None | Wrapped request list | `backend/apps/verification/urls.py:7-42`; `views.py:17-342` |
| GET | `/api/verification/admin/<uuid:verification_id>/document/` | Download submitted document | Superuser | Verification UUID | Attachment stream | `backend/apps/verification/urls.py:7-42`; `views.py:17-342` |
| POST | `/api/verification/admin/<uuid:verification_id>/action/` | Approve/reject verification | Superuser | `action=approve|reject`; rejection `reason` | Wrapped action result | `backend/apps/verification/urls.py:7-42`; `views.py:17-342` |
| GET | `/api/verification/admin/logs/` | Read admin action logs | Superuser | None | Audit-log records | `backend/apps/verification/urls.py:7-42`; `views.py:17-342` |

The root URL configuration also serves `/admin/` and the template-page GET routes declared in `backend/helpnet/urls.py:51-119`. Media URLs are served from the public media root only when `DEBUG` is enabled (`backend/helpnet/urls.py:121-122`).

## Data models

| Entity | Main fields and relationships |
|---|---|
| `User`, `UserProfile` | UUID user ID; name, unique email/phone, legacy role, location, picture, bio, birth date/gender, privacy/verification flags and timestamps. `active_profile` points to a profile; profiles belong to a user and have type, display name, status and NGO approval state; unique per user/type. (`backend/apps/users/models.py:62-184`) |
| `WasteCollector`, `WasteCollectorRating`, `WastePickupRequest` | Collector details and `shared_by` user; ratings link collector/user (unique pair); pickup requests link requester and optional collector and store waste, location, pickup preferences, status and notes. (`backend/apps/waste/models.py:7-180`) |
| `ProduceListing` | Farmer FK; produce/category, price/unit/quantity, availability, location, description and timestamps. (`backend/apps/farmer/models.py:6-35`) |
| `Rating` | Rater and rated-user FKs; score, comment and timestamps; unique rater/target pair. (`backend/apps/ratings/models.py:9-45`) |
| `Report` | Reporter and optional reported-user FKs; optional generic ContentType/object target; category, description, status and timestamps. (`backend/apps/reports/models.py:8-59`) |
| `DonorProfile`, `BloodRequest`, `DonationHistory` | Donor profile is one-to-one with user; blood group, area and availability. Request links requester and includes group, area, hospital, details, document and status. Donation links donor and one-to-one blood request. (`backend/apps/blood/models.py:6-116`) |
| `Notification` | UUID; user FK; message, action URL, type, read flag and creation time. (`backend/apps/notifications/models.py:7-27`) |
| `GoodsListing`, `GoodsInterest`, `GoodsConversation`, `GoodsMessage`, `GoodsReport` | Listing links seller and stores description/condition/price/location/image/status. Interest links listing/user (unique pair). Conversation links listing/owner/interested user (unique triplet, distinct participants); messages link conversation/sender. GoodsReport links listing/reporter and stores reason/description/status. (`backend/apps/goods/models.py:7-90`) |
| `HealthQuestion`, `HealthReply`, `HealthProfessional` | Questions link author; replies link question and author. Professional application may link user/reviewer and stores contact/credential/private document and verification fields. (`backend/apps/health/models.py:7-67`) |
| `VolunteerProfile`, `VolunteerProfileDocument`, `VolunteerOpportunity`, `VolunteerSignup`, `VolunteerAttendance`, `VolunteerMessage`, `VolunteerCertificate` | Profile is one-to-one with user; private documents link profiles. Opportunities link coordinator; signup, attendance, messages and certificates link users and events, with uniqueness constraints for relevant event/user pairs. (`backend/apps/volunteer/models.py:6-92`) |
| `VerificationRequest`, `AdminActionLog` | Verification request links user and reviewer and stores private document/type/status/rejection/review fields. Log links protected admin and optional target user and stores action/reference/reason/time. (`backend/apps/verification/models.py:10-95`) |

The `common` app currently has no models or routed feature.

## Auth and middleware

- DRF defaults to JWT authentication and `IsAuthenticated`; login returns access/refresh tokens, and logout blacklists the supplied refresh token. Access tokens last one day and refresh tokens 60 days (`backend/helpnet/settings.py:186-205`).
- Registration accepts only citizen/NGO account types. NGO profiles are approved by superusers; volunteer coordination requires an active approved NGO profile. Other routes use role, ownership, or superuser checks as described in the API table.
- Django admin uses Django's session authentication. Middleware includes CORS, security, sessions, common, CSRF, authentication, messages, and clickjacking (`backend/helpnet/settings.py:61-70`).
- CORS is configured to allow all origins. Frontend API calls use bearer tokens through the shared helper; invalid-token handling clears session data, and token refresh is not automatic.

## External services and integrations

| Service/configuration | Details |
|---|---|
| Database | MySQL outside tests; set `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`. Test invocation selects SQLite (`backend/helpnet/settings.py:99-122`). |
| Environment files | Settings read `.env` from the repository root or `backend/`; names in `backend/.env.example`. |
| Email | Console backend by default; optional SMTP configuration: `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`; reset links use `FRONTEND_BASE_URL` (`backend/helpnet/settings.py:209-219`). |
| Uploads | Local filesystem. Public media in `backend/media/`; sensitive verification, health credential and volunteer documents use separate private storage/download handlers. |
| Other libraries | ReportLab creates volunteer certificate PDFs; Pillow validates goods images. Cloudinary packages are declared but no Cloudinary storage configuration is present in settings. |
| Queue/cache | No queue or cache service configuration was found. |

## How to run

From the repository root, use a Python environment with the project requirements installed. Configure the database values in `backend/.env` (or the root `.env`) before a normal MySQL-backed run.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item backend\.env.example backend\.env
# Set DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, and DB_PORT in backend\.env.
python backend\manage.py migrate
python backend\manage.py runserver
```

Run backend tests with `pytest` (discovery is configured by `pytest.ini` to use `backend/`). Selenium/browser tests are in `tests/selenium/` and should be run explicitly, for example `pytest tests\selenium\test_navigation.py -v`, with a running site and compatible Chrome/Selenium setup. No npm install/build step is defined.

## Gaps and unclear areas

- The root README contains only a project title/tagline; a complete setup guide is not maintained there. The documented Selenium plan's example checkout path differs from this repository's `backend/manage.py` location.
- Settings hardcode `DEBUG=True`, a development secret key, and empty `ALLOWED_HOSTS`; CORS allows all origins. Production configuration is not complete (`backend/helpnet/settings.py:22-26,181`).
- Cloudinary dependencies are present but no corresponding storage configuration is active. Backups are documented as manual; no automated backup or restore drill is configured (`docs/backup-restore.md`).
- The blood donor search reads but does not apply its `available` parameter; blood request documents use ordinary public media storage. The ratings TODO notes that uniqueness is not scoped to an interaction; an unrated user's summary displays 5.0 while the average endpoint can return null.
- The volunteer `/api/volunteer/certificates/` POST handler expects an `event_id` that is not present in the route. `GoodsReport` is modeled/serialized, but its reporting route creates a generic `Report`.
- Health professional application checks use the legacy Citizen role, while profile creation does not itself assign those legacy roles. `health-verification-admin.js` is present but its page include is commented out; `app.js`, `admin-dashboard.js`, and `volunteer-profile.js` do not appear as active page includes (the volunteer profile page has inline script).
- Frontend request/debug logging remains in shared and feature scripts. Localization coverage is inconsistent across pages.
- Testing documentation reports historical results, not a current run: Selenium results report 52 passing tests with known scope exclusions; separate triage notes report prior pytest and Selenium failures. Current full-suite status was not verified for this summary.

# HELPNET API Documentation

Source of truth: Django URL configuration and API views in `backend/apps/` and `backend/helpnet/urls.py`. Paths in the endpoint inventory include `/api/`; browser template routes are separate.

## Authentication and conventions

- JWT bearer token: `Authorization: Bearer <access-token>`. Most API views require an authenticated user.
- Registration, login, and password reset are public. Superuser-only review/moderation and owner/participant-scoped routes are marked in the endpoint inventory.
- Configured token lifetimes are one day for access and 60 days for refresh. Browser token refresh is not automatic.
- Custom endpoints commonly return `{success, data, message}`; generic DRF views may return serializer JSON. Validation and authentication use HTTP error responses.
- Multipart requests carry documents. Private downloads use authenticated endpoints rather than public media URLs.

## API endpoints

All paths below are mounted below `/api/` unless the full path is shown. JWT authentication and `IsAuthenticated` are the DRF defaults; public and role/owner-limited exceptions are noted. Successful custom endpoints usually return `{success, data, message}`; generic DRF views return serializer JSON directly. Error responses include framework validation/authentication errors. Route line references point to app URL configurations; app prefixes are composed in `backend/helpnet/urls.py:26-50`.

| Method | Path | Description | Auth required | Request params/body | Response | File:line |
|---|---|---|---|---|---|---|
| GET | `/api/` | API status/welcome and endpoint listing | No | None | JSON status object | `backend/helpnet/urls.py:13-21` |
| POST | `/api/auth/register/` | Register citizen or NGO | No | `full_name,email,phone_number,password,location,account_type` | 201; user and profiles; NGO must submit verification before approval | `backend/apps/users/urls.py`; `backend/apps/users/views.py` |
| POST | `/api/auth/login/` | Login with email or phone | No | `identifier,password` | User data and access/refresh JWTs | `backend/apps/users/urls.py:16-43`; `views.py:86-199` |
| POST | `/api/auth/logout/` | Blacklist refresh token | Yes | `refresh` | Success with null data | `backend/apps/users/urls.py:16-43`; `views.py:202-381` |
| POST | `/api/auth/password-reset/` | Request password reset email | No | `email` | Generic success, including unknown email | `backend/apps/users/urls.py:16-43`; `views.py:202-381` |
| POST | `/api/auth/password-reset-confirm/` | Set new password from reset token | No | `uid,token,new_password` | Success with null data | `backend/apps/users/urls.py:16-43`; `views.py:202-381` |
| GET, PATCH | `/api/auth/me/` | Read/update current user profile | Yes | PATCH writable profile fields | Wrapped profile object | `backend/apps/users/urls.py:16-43`; `views.py:383-437` |
| GET, POST | `/api/auth/profiles/` | List/create profiles, including pending NGO profiles | Yes | POST `profile_type`, optional `display_name,details` | Wrapped profile list/object | `backend/apps/users/urls.py:16-43`; `views.py` profile endpoints |
| GET, PUT, PATCH, DELETE | `/api/auth/profiles/<int:id>/` | Read/update/deactivate own profile | Yes; owner-scoped | Profile serializer fields and supported role details; DELETE has no body | Serializer object; DELETE 204 | `backend/apps/users/urls.py:16-43`; `views.py` profile endpoints |
| POST | `/api/auth/profiles/<int:id>/reactivate/` | Reactivate an owned inactive profile | Yes; owner-scoped | No body | Reactivated profile object | `backend/apps/users/urls.py`; `views.py` profile lifecycle |
| GET, POST | `/api/auth/profiles/<int:profile_id>/ngo-verification/` | Read or submit the selected active NGO profile's verification application | Yes; profile owner, active NGO profile required | Multipart: organization name, registration number, address, official email, phone, representative name; required registration certificate; optional official, authorization, and supporting documents (PDF/JPG/PNG; max 10 MiB each) | NGO information, verification status/reason/timestamps, and private document names/download endpoints; resubmission replaces files of the same type after rejection/additional-documents request | `backend/apps/users/urls.py`; `backend/apps/users/views.py` |
| GET | `/api/auth/ngo-verification-documents/<uuid:document_id>/` | Download a submitted verification document without exposing a public media URL | Owner or superuser | Document UUID | Private attachment response; other users receive 403 | `backend/apps/users/urls.py`; `backend/apps/users/views.py` |
| GET, PUT | `/api/auth/active-profile/` | Read/select active profile | Yes | PUT `profile_id` | Wrapped profile or null | `backend/apps/users/urls.py:16-43`; `views.py:438-538` |
| GET | `/api/auth/ngo-profiles/pending/` | List pending, under-review, and additional-documents-required NGO applications | Superuser | None | Organization details, status/reason/timestamps, and protected document links | `backend/apps/users/urls.py`; `backend/apps/users/views.py` |
| PATCH | `/api/auth/ngo-profiles/<int:profile_id>/approval/` | Record NGO review status | Superuser | `verification_status=under_review|approved|rejected|additional_documents_required`; `review_reason` required for rejection/additional documents | Updated verification and legacy approval statuses plus review timestamp; approval requires complete organization details and registration certificate | `backend/apps/users/urls.py`; `backend/apps/users/views.py` |
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
| GET, POST | `/api/blood/requests/` | List open requests/create a request | Yes | POST `blood_group,area,hospital`, optional `details,supporting_document` (multipart) | Wrapped request; creates notifications for matching donors; document URLs are returned only to the requester and superusers | `backend/apps/blood/urls.py`; `views.py` |
| GET | `/api/blood/requests/<uuid:request_id>/document/` | Download a supporting document | Yes; requester or superuser | Request UUID | Authenticated attachment stream | `backend/apps/blood/urls.py`; `views.py` |
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
| GET, POST | `/api/volunteer/certificates/` | List the signed-in volunteer's certificates or certificates coordinated by the signed-in NGO; issue a certificate using the request body | Yes; coordinator for POST | POST `event_id,volunteer_id`; completed attendance required | Wrapped certificate list/object; the generic POST route validates `event_id` from the body | `backend/apps/volunteer/urls.py:5-19`; `views.py:20-359` |
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



## Limitations

- Production URLs, rate limits, and API versioning are not configured in this documentation.
- The generic volunteer certificate POST accepts `event_id` in the request body; the event-specific route carries it in the URL.
- Production MySQL and external email delivery were not part of this test run.

# Sprint 4 volunteer acceptance decisions

This note records the acceptance rules used by the volunteer implementation and its API tests.

## Opportunities and signup (ST 28–29)

- Opportunity fields: title, description, event date, location, required volunteer count, open/closed status, NGO coordinator, and creation time.
- Only NGO accounts may create and manage their own opportunities. Authenticated users can browse open opportunities; volunteer accounts can sign up.
- Signup is allowed only while an event is open and has an unfilled slot. Each volunteer may sign up once per opportunity; a database uniqueness constraint backs the API check.
- Browse cards show title, date, location, description, coordinator, status, and signup count against capacity. Selecting an opportunity opens the details page with the signup action.

## Signup flow review (FR 4.1)

- Technical review: PASS on 8 Oct 2026. The API and automated tests verify NGO-only posting, Citizen refusal, authenticated browsing, volunteer-only signup, closed-event and capacity rejection, and duplicate prevention.
- The detail page loads the selected opportunity from the detail API and submits signup through the same guarded endpoint.
- Business-owner acceptance is still required; this technical review does not represent stakeholder approval.

## Volunteer profile and attendance (ST 30–31)

- Profile fields: skills, availability, location, blood group, and certificate name/link notes. One profile belongs to each account.
- Supporting document uploads accept PDF, JPEG, or PNG files up to 5 MiB each. Files are stored outside public media. Only the profile owner with a Volunteer role may upload, list, or download their documents; download URLs require authentication.
- An event coordinator can record one check-in and one check-out for a signed-up volunteer. Both are server-generated UTC timestamps. Check-out requires check-in, and repeated actions are rejected without changing the first timestamp.

## Event messages and certificates (ST 32–33)

- The event coordinator and signed-up volunteers may read and post messages. Each message stores its event, sender, body, and server timestamp; non-members are refused.
- A coordinator may issue one certificate to a signed-up volunteer only after both check-in and check-out are recorded. Volunteers and the issuing coordinator can view the certificate.
- Certificates have a browser print view with a landscape print stylesheet and remain available as PDF downloads.

## Search and export (ST 34–35 / FR 9.4)

- NGO coordinators search volunteer profiles by case-insensitive skill, availability, and location text, in any combination. Participation history supports `yes` (one or more signups) and `no` (no signups); `event_id` narrows results to participation in a particular opportunity.
- The volunteer database is admin-only. CSV export is admin-only and accepts the same skill, availability, and location filters.
- CSV columns are Full name, Skills, Availability, Location, Signup count, and Completed events. Email, phone number, blood group, certificate notes, and uploaded file paths are excluded as private data.
- CSV is UTF-8 with a BOM for spreadsheet compatibility. Filter tests use fixed volunteers and an event with known signup/attendance state.
- Sign-off: reviewed the CSV fields against FR 9.4. The CSV contains volunteer directory and participation information for administration, and excludes direct contact details and sensitive blood/document data.

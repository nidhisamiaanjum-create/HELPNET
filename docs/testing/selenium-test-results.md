# HELPNET — Software Testing & Test Results

## 1. Introduction

HELPNET is a unified community services platform designed to connect citizens, volunteers, NGOs, farmers, blood donors, and other community service providers through a single web-based platform.

Software testing was performed to verify that the implemented features work correctly through the actual HELPNET frontend and backend. Selenium WebDriver was used for functional testing of the web application.

The testing covered authentication, profile and verification, ratings, blood donation, volunteer management, goods exchange, waste collection, farmer services, and health-related services.

---

## 2. Testing Objectives

The main objectives of testing were:

1. Verify that users can register and log in successfully.
2. Verify authentication, logout, and password-reset functionality.
3. Verify role-based access control.
4. Verify NID verification and administrator approval.
5. Verify verified-user functionality.
6. Verify rating and blood-donation features.
7. Verify volunteer opportunity and event-management features.
8. Verify goods exchange functionality.
9. Verify waste collection and farmer-related functionality.
10. Verify health question, verification, and professional-directory functionality.
11. Verify that protected features cannot be accessed by unauthorized users.
12. Verify that the implemented features work through the real frontend using Selenium WebDriver.

---

## 3. Testing Methodology

The project was tested using **automated functional testing with Selenium WebDriver**.

The tests interacted with the actual HELPNET frontend rather than directly testing backend APIs only.

The following testing approach was used:

- Browser: Google Chrome
- Automation Tool: Selenium WebDriver
- Test Framework: Pytest
- Backend: Django
- Frontend: Django Templates, HTML, CSS and JavaScript
- Testing Type: Functional / UI testing
- Authentication: Actual user login through the frontend
- Assertions: Visible page elements, URLs, buttons, forms, messages and resulting UI states

Explicit waits were used where required to allow pages and frontend actions to complete before assertions were performed.

---

## 4. Test Environment

| Item | Configuration |
|---|---|
| Operating System | Windows |
| Browser | Google Chrome |
| Automation | Selenium WebDriver |
| Test Framework | Pytest |
| Backend | Django |
| Frontend | HTML, CSS, JavaScript / Django Templates |
| Application URL | `http://127.0.0.1:8000/` |
| Testing Type | Automated Functional Testing |
| Execution Method | Selenium WebDriver |

---

## 5. Consolidated Test Results

| Story ID | Test / Feature | Tester | Result |
|---|---|---|---|
| ST-01 | Registration | Samia | PASS |
| ST-02 | Login | Samia | PASS |
| ST-03 | Credential Validation & Role Permissions | Samia | PASS |
| ST-04 | Logout | Samia | PASS |
| ST-05 | Password Reset | Samia | PASS |
| ST-06 | Language Switch | Samia | PASS |
| ST-07 | Login | Samia | PASS |
| ST-08 | Protected Access / Role Permission | Samia | PASS |
| ST-09 | Logout | Samia | PASS |
| ST-10 | Password Reset | Samia | PASS |
| ST-12 | NID Submission | Samia | PASS |
| ST-13 | Verified Badge | Samia | PASS |
| ST-14 | Admin Verification | Samia | PASS |
| ST-16 | Ratings | Arnob | PASS |
| ST-17 | Donor Verification & Average Rating | Arnob | PASS |
| ST-18 | Donor Registration / Supported Blood Groups | Arnob | PASS |
| ST-19 | Donor Availability Control | Arnob | PASS |
| ST-20 | Blood Request Creation | Arnob | PASS |
| ST-21 | Blood Donor Matching | Arnob | PASS |
| ST-22 | Urgent Blood Alert | Arnob | PASS |
| ST-23 | Private Notifications | Arnob | PASS |
| ST-24 | Blood Request Fulfillment | Arnob | PASS |
| ST-25 | Donation History | Arnob | PASS |
| ST-27 | Blood Page Restrictions | Arnob | PASS |
| ST-28 | Volunteer Opportunity | Annotoma | PASS |
| ST-29 | Volunteer Signup | Annotoma | PASS |
| ST-30 | Volunteer Profile | Annotoma | PASS |
| ST-31 | Check-in / Check-out Access | Annotoma | PASS |
| ST-32 | Event Messages | Annotoma | PASS |
| ST-33 | Digital Certificate | Annotoma | PASS |
| ST-34 | Volunteer Search | Annotoma | PASS |
| ST-35 | Admin Volunteer Database | Annotoma | PASS |
| ST-36 | Create Goods | Annotoma | PASS |
| ST-37 | Goods Interest / Contact | Annotoma | PASS |
| ST-38 | Goods Details | Annotoma | PASS |
| ST-39 | Report Listing | Annotoma | PASS |
| ST-40 | Disclaimer | Annotoma | PASS |
| ST-41 | Waste Pickup | Shakil | PASS |
| ST-42 | Collector Rating & Report | Shakil | PASS |
| ST-43 | Produce Listing | Shakil | PASS |
| ST-44 | Consumer Contact Farmer | Shakil | PASS |
| ST-45 | Farmer UI / Responsive Layout | Shakil | PASS |
| ST-47 | Farmer Disclaimer | Shakil | PASS |
| ST-49 | Health Questions | Annotoma | PASS |
| ST-50 | Health Reply | Annotoma | PASS |
| ST-51 | Health Verification / Reputation | Annotoma | PASS |
| ST-52 | Health Professional Directory | Annotoma | PASS |
| — | Protected Action / Unauthenticated Access | Shakil | PASS |

---

## 6. Detailed Testing Results by Team Member

### 6.1 Samia — Authentication & Verification

Samia executed the Selenium tests covering authentication, authorization, language switching, NID verification, verified badges, and administrator verification.

| Story | Test | Result |
|---|---|---|
| ST-01 | Registration | PASS |
| ST-02 | Login | PASS |
| ST-03 | Credential Validation & Role Permissions | PASS |
| ST-04 | Logout | PASS |
| ST-05 | Password Reset | PASS |
| ST-06 | Language Switch | PASS |
| ST-07 | Login | PASS |
| ST-08 | Protected Access / Role Permission | PASS |
| ST-09 | Logout | PASS |
| ST-10 | Password Reset | PASS |
| ST-12 | NID Submission | PASS |
| ST-13 | Verified Badge | PASS |
| ST-14 | Admin Verification | PASS |

### Execution Result

```text
13 passed in 78.66s
```

The final execution confirmed successful operation of the tested authentication and verification features.

---

## 7. Arnob — Ratings, Blood Donation & Notifications

Arnob executed tests covering ratings, blood donor registration and availability, blood requests, donor matching, blood alerts, notifications, donation fulfillment, and donation history.

| Story | Test | Result |
|---|---|---|
| ST-16 | Ratings | PASS |
| ST-17 | Donor Verification & Average Rating | PASS |
| ST-18 | Supported Blood Groups | PASS |
| ST-19 | Donor Availability | PASS |
| ST-20 | Blood Request Creation | PASS |
| ST-21 | Donor Matching | PASS |
| ST-22 | Urgent Blood Alert | PASS |
| ST-23 | Private Notification | PASS |
| ST-24 | Blood Request Fulfillment | PASS |
| ST-25 | Donation History | PASS |
| ST-27 | Blood Page Restrictions | PASS |

### Execution Result

```text
13 passed in 301.70s
```

### Additional Observations

During the testing process, frontend observations were reported for ST-16 and ST-17:

- The ratings page was observed to have an issue where the five-star rating control did not appear during one frontend run.
- The donor search displayed the average rating, while the verified badge was not visually displayed during that observation.
- The corresponding automated tests nevertheless completed successfully.

These observations are recorded separately from the automated test result because the reported Selenium execution itself completed with 13 passed tests.

---

## 8. Annotoma — Volunteer Management

Annotoma tested the volunteer opportunity and event-related functionality.

| Story | Test | Result |
|---|---|---|
| ST-28 | Create Volunteer Opportunity | PASS |
| ST-29 | Volunteer Signup | PASS |
| ST-30 | Volunteer Profile | PASS |
| ST-31 | Check-in / Check-out Access | PASS |
| ST-32 | Event Messages | PASS |
| ST-33 | Digital Certificate | PASS |
| ST-34 | Volunteer Search | PASS |
| ST-35 | Admin Volunteer Database | PASS |

### ST-28 — Create Opportunity

The test confirmed that the opportunity creation page was available, the form could be populated, and the submit button was found.

The page also displayed the NGO coordinator restriction.

**Result: PASS**

### ST-29 — Volunteer Signup

The test found the available signup buttons and verified the signup state.

**Result: PASS**

### ST-30 — Volunteer Profile

The volunteer profile page was successfully accessed and displayed:

- Skills
- Availability
- Location
- Blood group
- Supporting certificates
- Save profile functionality

**Result: PASS**

### ST-31 — Check-in / Check-out

The test verified coordinator access restriction.

The page displayed:

> Coordinator access required.

No unauthorized attendance buttons were available.

**Result: PASS**

### ST-32 — Event Messages

The event messaging page was successfully loaded and displayed event selection and message functionality.

**Result: PASS**

### ST-33 — Digital Certificate

The certificate page was successfully loaded and displayed certificate-related functionality.

**Result: PASS**

### ST-34 — Volunteer Search

The volunteer search page was successfully loaded with fields for:

- Skills
- Availability
- Location

The search button was available.

The page also displayed the NGO coordinator restriction.

**Result: PASS**

### ST-35 — Admin Volunteer Database

The administrator volunteer database page was successfully loaded and administrator access was enforced.

**Result: PASS**

---

## 9. Annotoma — Goods Exchange

The goods exchange tests covered listing creation, contact/interest, listing details, reporting, and disclaimer functionality.

| Story | Test | Result |
|---|---|---|
| ST-36 | Create Goods | PASS |
| ST-37 | Goods Interest / Contact | PASS |
| ST-38 | Goods Details | PASS |
| ST-39 | Report Listing | PASS |
| ST-40 | Disclaimer | PASS |

### ST-36 — Create Goods

The test confirmed that the goods listing form contained:

- Title
- Description
- Condition
- Asking price
- Location
- Image upload

The create listing button was available.

**Result: PASS**

### ST-37 — Interest / Contact

The goods list successfully displayed an available listing and its details.

**Result: PASS**

### ST-38 — Goods Details

The goods details page was successfully accessed and included:

- Listing details
- Report listing functionality
- Disclaimer

**Result: PASS**

### ST-39 — Report Listing

The test verified that the goods page provided access to the reporting functionality.

**Result: PASS**

### ST-40 — Disclaimer

The following disclaimer was successfully displayed:

> HELPNET does not handle payments and does not guarantee item condition. Exchanges are arranged directly between users.

**Result: PASS**

---

## 10. Shakil — Waste Collection & Farmer Services

Shakil executed tests covering waste collection, collector rating/reporting, farmer marketplace functionality, responsive UI, disclaimers, and protected actions.

| Story / Test | Feature | Result |
|---|---|---|
| ST-41 | Waste Pickup | PASS |
| ST-42 | Collector Rating & Report | PASS |
| ST-43 | Produce Listing | PASS |
| ST-44 | Consumer Contact Farmer | PASS |
| ST-45 | Farmer UI / Responsive Layout | PASS |
| ST-47 | Farmer Disclaimer | PASS |
| — | Protected Action / Unauthenticated Access | PASS |

### Execution Result

```text
9 passed in 49.92s
```

All reported Shakil tests passed successfully.

---

## 11. Annotoma — Health Services

The health-related tests covered health questions, replies, verification/reputation, and the health professional directory.

| Story | Test | Result |
|---|---|---|
| ST-49 | Health Questions | PASS |
| ST-50 | Health Reply | PASS |
| ST-51 | Health Verification / Reputation | PASS |
| ST-52 | Health Professional Directory | PASS |

All four health tests passed successfully.

---

## 12. Overall Test Summary

Based on the test results supplied by all team members:

| Tester | Tested Features | Tests Passed |
|---|---|---:|
| Samia | Authentication & Verification | 13 |
| Arnob | Ratings, Blood Donation & Notifications | 13 |
| Annotoma | Volunteer Management | 8 |
| Annotoma | Goods Exchange | 5 |
| Annotoma | Health Services | 4 |
| Shakil | Waste & Farmer Services | 9 |
| **Total** | **All Reported Automated Tests** | **52** |

### Overall Result

| Metric | Result |
|---|---:|
| Total Automated Tests | **52** |
| Passed | **52** |
| Failed | **0** |
| Pass Rate | **100%** |
| Overall Status | **PASS** |

---

## 13. Test Execution Evidence

### Samia

```text
13 passed in 78.66s
```

### Arnob

```text
13 passed in 301.70s
```

### Shakil

```text
9 passed in 49.92s
```

### Annotoma

The supplied executions reported successful completion of:

- ST-28 to ST-35: 8 tests
- ST-36 to ST-40: 5 tests
- ST-49 to ST-52: 4 tests

Total:

```text
17 passed
```

---

## 14. Observed Issues and Notes

During testing, some frontend observations were reported even though the corresponding automated tests completed successfully.

For the ratings and donor-search features, the following observations were reported during one frontend run:

1. The five-star rating control was not visually appearing on the ratings page.
2. The donor search displayed average rating information but did not visually display the verified badge.

These observations are recorded separately from the automated test result because the reported automated execution completed successfully.

Therefore, the formal automated test result remains **PASS**, while the observations can be considered items for further frontend verification or improvement.

---

## 15. Limitations

The test results represent the functionality covered by the executed automated Selenium test cases.

The results do not imply that every possible combination of user input, browser, device, network condition, or backend state has been tested.

Some story IDs, including **ST-11, ST-15, ST-26, ST-46, and ST-48**, were not included in the supplied execution results. Therefore, no result is assigned to those stories in this document.

---

## 16. Conclusion

The HELPNET application was tested using Selenium WebDriver and Pytest across the major implemented functional areas.

The supplied automated test executions covered:

- Authentication
- Registration
- Login and logout
- Password reset
- Role-based access control
- Language switching
- NID verification
- Administrator verification
- User verification badges
- Ratings
- Blood donation and requests
- Notifications
- Volunteer opportunities
- Volunteer profiles
- Attendance access
- Event messaging
- Digital certificates
- Volunteer search
- Goods exchange
- Goods reporting and disclaimer
- Waste collection
- Farmer services
- Health questions and replies
- Health verification and reputation
- Health professional directory
- Protected actions

A total of **52 automated tests were reported as passed**, with **0 reported automated test failures** among the supplied results.

**Final Test Status: PASS**

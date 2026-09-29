# HELPNET — Selenium Test Plan

## 1. Purpose

This document defines the Selenium testing plan for the completed HELPNET features.

The testing will verify that the implemented features work correctly through the web interface, including valid input, invalid input, authentication, permissions, and user-visible results.

Mokarram's unfinished stories are not included in this testing plan.

---

## 2. Testing Technology

* Django 5.2.x
* Django REST Framework
* MySQL
* HTML/CSS/JavaScript frontend
* Selenium
* Pytest
* pytest-django

---

## 3. Test Setup

Open PowerShell:

powershell
cd E:\HELPNET
.\.venv\Scripts\Activate.ps1


Install the testing packages:

powershell
pip install selenium pytest pytest-django


Start the Django server:

powershell
python manage.py runserver


Keep the server running while Selenium tests are executed.

---

# 4. Testing Responsibilities

## 4.1 Samia

### Assigned Stories

* ST-01 to ST-10
* ST-12
* ST-13
* ST-14

### Test Areas

#### Authentication

Test:

1. User registration with valid information.
2. Registration with missing required fields.
3. Registration with invalid information.
4. Registration with duplicate email/phone where applicable.
5. Login with valid credentials.
6. Login with invalid credentials.
7. Access to protected pages without login.
8. Logout functionality.
9. Authentication/session behavior.
10. Role-based access where applicable.

### Profile

Test:

1. Open user profile.
2. Check that saved user information is displayed.
3. Update profile information.
4. Submit invalid profile information.
5. Verify that updated information is saved.

### Verification

Test:

1. Open verification functionality.
2. Submit valid verification information.
3. Check required-field validation.
4. Check verification status.
5. Check that unauthorized users cannot perform restricted verification actions.

### Test command

powershell
pytest tests\selenium\test_samia.py -v

---

# 5. Arnob

## Assigned Stories

* ST-16 to ST-25
* ST-27

## Test Areas

### Ratings

Test:

1. Logged-in user can submit a rating.
2. Rating value is accepted within the allowed range.
3. Invalid rating is rejected.
4. Required rating information is validated.
5. Submitted rating is displayed correctly.
6. Rating information is shown to the appropriate user.

### Blood Donation

Test:

1. Open blood donation functionality.
2. Submit valid blood-related information.
3. Check required fields.
4. Submit incomplete information.
5. Check that invalid information is rejected.
6. Verify that submitted information appears correctly.
7. Check access restrictions where applicable.

### Notifications

Test:

1. Generate an action that should create a notification.
2. Check that the notification appears.
3. Verify that the correct user receives the notification.
4. Open/read the notification where applicable.
5. Check notification behavior for invalid/unauthorized access.

### Test command

powershell
pytest tests\selenium\test_arnob.py -v

---

# 6. Annotoma

## Assigned Stories

* ST-28 to ST-40
* ST-49 to ST-52

## Test Areas

### Volunteer

Test:

1. Open volunteer functionality.
2. Create a valid volunteer entry/application.
3. Check required fields.
4. Submit incomplete information.
5. Check invalid input.
6. View volunteer information.
7. Check that unauthorized actions are blocked where applicable.

### Second-hand Goods

Test:

1. Create a second-hand goods listing.
2. Submit valid listing information.
3. Check required fields.
4. Submit incomplete/invalid listing information.
5. View the created listing.
6. Update listing where applicable.
7. Delete listing where applicable.
8. Check unauthorized actions.

### Health

Test:

1. Open the health functionality.
2. Submit valid information.
3. Check required fields.
4. Submit invalid/incomplete information.
5. Verify that saved information is displayed correctly.
6. Check access restrictions where applicable.

### Test command

powershell
pytest tests\selenium\test_annotoma.py -v

---

# 7. Shakil

## Assigned Stories

* ST-41 to ST-45
* ST-47

## Test Areas

### Waste Management

Test:

1. Open waste-management functionality.
2. Submit valid waste-related information.
3. Check required fields.
4. Submit incomplete information.
5. Submit invalid information.
6. Verify saved information.
7. Check unauthorized actions where applicable.

### Farmer Marketplace

Test:

1. Create a farmer marketplace listing.
2. Submit valid listing information.
3. Check required fields.
4. Submit invalid/incomplete information.
5. View marketplace listing.
6. Update listing where applicable.
7. Delete listing where applicable.
8. Check unauthorized access/actions.

### Test command

powershell
pytest tests\selenium\test_shakil.py -v

---

# 8. Common Test Rules

Each tester should check both positive and negative cases.

### Positive test

Use valid information and verify that the expected operation succeeds.

Example:

text
Valid login
→ Login succeeds
→ User dashboard opens

### Negative test

Use invalid or incomplete information and verify that the system handles it correctly.

Example:

text
Invalid login
→ Login fails
→ Error message is displayed
→ User is not logged in

### Authentication test

Check that protected functionality cannot be used by an unauthenticated user.

### Permission test

Check that users cannot perform actions that are not allowed for their role.

---

# 9. Test Result Recording

Create:

text
docs/testing/selenium-test-results.md

Record every test using this format:

| Story | Test Case            | Result    | Notes |
| ----- | -------------------- | --------- | ----- |
| ST-01 | Valid registration   | PASS/FAIL |       |
| ST-01 | Invalid registration | PASS/FAIL |       |
| ST-02 | Valid login          | PASS/FAIL |       |
| ST-02 | Invalid login        | PASS/FAIL |       |

Do not remove failed tests from the document.

If a failed test is fixed, update the result:

text
FAIL → PASS

and write the fix in the Notes column.

---

# 10. Final Test Commands

### Samia

powershell
pytest tests\selenium\test_samia.py -v

### Arnob

powershell
pytest tests\selenium\test_arnob.py -v

### Annotoma

powershell
pytest tests\selenium\test_annotoma.py -v


### Shakil

powershell
pytest tests\selenium\test_shakil.py -v

---

# 11. Git Tracking

The test plan should be stored in:

text
docs/testing/selenium-test-plan.md

After adding it:

powershell
git add docs/testing/selenium-test-plan.md
git commit -m "docs: add Selenium test plan"
git push

The actual test results should be tracked separately in:

text
docs/testing/selenium-test-results.md


This keeps the **test plan** and **actual test results** separate.
